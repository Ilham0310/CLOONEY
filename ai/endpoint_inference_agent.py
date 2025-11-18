"""
Endpoint Inference Agent
Uses Gemini to infer endpoint semantics and behavior from grouped network messages.
"""

import json
import logging
from typing import Dict, Any, List, Optional
from .gemini_client import get_client, is_ai_enabled

logger = logging.getLogger(__name__)


def infer_endpoint_spec_with_gemini(
    messages: List[Dict[str, Any]],
    operation_name: Optional[str] = None
) -> Dict[str, Any]:
    """
    Infer endpoint specification from grouped network messages using Gemini.
    
    Args:
        messages: List of related network messages (requests/responses) for one operation
        operation_name: Optional operation name (e.g., "create_task", "update_project")
        
    Returns:
        Dictionary with endpoint specification:
        {
            "method": "GET|POST|PUT|DELETE",
            "path": "/api/1.0/entities",
            "operation": "create_task|update_project|list_tasks|get_task|delete_task",
            "description": "Human-readable description",
            "expected_status_codes": [200, 201, 400, 404],
            "request_schema": {...},  # Inferred request body schema
            "response_schema": {...},  # Inferred response body schema
            "path_parameters": [...],  # e.g., ["id"]
            "query_parameters": [...]  # e.g., ["project_id", "completed"]
        }
    """
    if not is_ai_enabled():
        logger.warning("AI not enabled, using fallback endpoint inference")
        return _fallback_endpoint_inference(messages, operation_name)
    
    client = get_client()
    if not client:
        return _fallback_endpoint_inference(messages, operation_name)
    
    # Prepare messages for prompt
    messages_str = json.dumps(messages[:20], indent=2)  # Limit to 20 messages
    
    # Build prompt
    prompt = f"""You are analyzing network traffic to reverse-engineer REST API endpoint specifications.

I have captured network messages (requests and responses) for an operation called "{operation_name or 'operation'}".

Here are the captured messages:
{messages_str}

Please analyze these messages and infer:
1. HTTP method (GET, POST, PUT, DELETE)
2. Endpoint path (e.g., /api/1.0/tasks, /api/1.0/projects/{{id}})
3. Operation type (create, read, update, delete, list)
4. Expected HTTP status codes
5. Request body schema (if applicable)
6. Response body schema
7. Path parameters (e.g., {{id}} in the path)
8. Query parameters (if any)

Return a JSON object with this structure:
{{
    "method": "GET|POST|PUT|DELETE",
    "path": "/api/1.0/entities",
    "operation": "create_entity|update_entity|get_entity|list_entities|delete_entity",
    "description": "Human-readable description of what this endpoint does",
    "expected_status_codes": [200, 201, 400, 404],
    "request_schema": {{
        "type": "object",
        "properties": {{...}},
        "required": [...]
    }},
    "response_schema": {{
        "type": "object",
        "properties": {{...}}
    }},
    "path_parameters": ["id"],
    "query_parameters": ["filter", "sort"]
}}
"""
    
    schema_description = """{
    "method": "string",
    "path": "string",
    "operation": "string",
    "description": "string",
    "expected_status_codes": "array of integers",
    "request_schema": "object",
    "response_schema": "object",
    "path_parameters": "array of strings",
    "query_parameters": "array of strings"
}"""
    
    try:
        result = client.structured_call(prompt, schema_description)
        logger.info(f"Inferred endpoint spec for {result.get('operation', operation_name)} using Gemini")
        return result
    except Exception as e:
        logger.error(f"Error inferring endpoint spec with Gemini: {e}")
        logger.info("Falling back to heuristic inference")
        return _fallback_endpoint_inference(messages, operation_name)


def _fallback_endpoint_inference(
    messages: List[Dict[str, Any]],
    operation_name: Optional[str] = None
) -> Dict[str, Any]:
    """
    Fallback heuristic endpoint inference when AI is not available.
    
    Args:
        messages: List of network messages
        operation_name: Optional operation name
        
    Returns:
        Inferred endpoint specification
    """
    if not messages:
        return {
            "method": "GET",
            "path": "/api/1.0/unknown",
            "operation": operation_name or "unknown",
            "description": "Inferred from network traffic",
            "expected_status_codes": [200],
            "request_schema": {},
            "response_schema": {},
            "path_parameters": [],
            "query_parameters": []
        }
    
    # Extract method from first message
    first_msg = messages[0]
    method = first_msg.get("method", "GET").upper()
    
    # Extract path
    path = first_msg.get("url", first_msg.get("path", "/api/1.0/unknown"))
    # Normalize path
    if "?" in path:
        path = path.split("?")[0]
    
    # Infer operation from method and path
    operation = _infer_operation(method, path, operation_name)
    
    # Extract request/response bodies
    request_body = first_msg.get("request", {}).get("body") or first_msg.get("body")
    response_body = first_msg.get("response", {}).get("body") or first_msg.get("response")
    
    # Extract status codes
    status_codes = []
    for msg in messages:
        status = msg.get("response", {}).get("status") or msg.get("status_code")
        if status and status not in status_codes:
            status_codes.append(status)
    if not status_codes:
        status_codes = [200] if method == "GET" else [201]
    
    # Extract path parameters (simple heuristic: look for {id} patterns)
    path_parameters = []
    if "{id}" in path or "/" in path:
        parts = path.split("/")
        for part in parts:
            if part.startswith("{") and part.endswith("}"):
                path_parameters.append(part[1:-1])
    
    # Extract query parameters
    query_parameters = []
    for msg in messages:
        url = msg.get("url", "")
        if "?" in url:
            query_str = url.split("?")[1]
            params = query_str.split("&")
            for param in params:
                key = param.split("=")[0]
                if key and key not in query_parameters:
                    query_parameters.append(key)
    
    return {
        "method": method,
        "path": path,
        "operation": operation,
        "description": f"{method} {path} - {operation}",
        "expected_status_codes": status_codes,
        "request_schema": _infer_schema_from_body(request_body) if request_body else {},
        "response_schema": _infer_schema_from_body(response_body) if response_body else {},
        "path_parameters": path_parameters,
        "query_parameters": query_parameters
    }


def _infer_operation(method: str, path: str, operation_name: Optional[str] = None) -> str:
    """Infer operation name from HTTP method and path."""
    if operation_name:
        return operation_name
    
    path_lower = path.lower()
    entity = path.split("/")[-1].split("{")[0]  # Extract entity from path
    
    if method == "GET":
        if "{id}" in path or "/" in path.split("/")[-1]:
            return f"get_{entity}"
        else:
            return f"list_{entity}s"
    elif method == "POST":
        return f"create_{entity}"
    elif method == "PUT":
        return f"update_{entity}"
    elif method == "DELETE":
        return f"delete_{entity}"
    else:
        return f"{method.lower()}_{entity}"


def _infer_schema_from_body(body: Any) -> Dict[str, Any]:
    """Infer JSON schema from a request/response body."""
    if not body:
        return {}
    
    if isinstance(body, str):
        try:
            body = json.loads(body)
        except json.JSONDecodeError:
            return {}
    
    if not isinstance(body, dict):
        return {"type": type(body).__name__}
    
    schema = {
        "type": "object",
        "properties": {},
        "required": []
    }
    
    for key, value in body.items():
        if value is not None:
            schema["properties"][key] = {
                "type": _json_type_to_schema_type(type(value).__name__)
            }
        else:
            schema["properties"][key] = {"type": "string", "nullable": True}
    
    return schema


def _json_type_to_schema_type(python_type: str) -> str:
    """Convert Python type name to JSON schema type."""
    type_map = {
        "str": "string",
        "int": "integer",
        "float": "number",
        "bool": "boolean",
        "list": "array",
        "dict": "object"
    }
    return type_map.get(python_type, "string")

