"""
Schema Inference Agent
Uses Gemini to infer entity schemas and field properties from captured network traffic.
"""

import json
import logging
from typing import Dict, Any, List, Optional
from .gemini_client import get_client, is_ai_enabled

logger = logging.getLogger(__name__)


def infer_schema_with_gemini(
    samples: List[Dict[str, Any]],
    ui_hints: Optional[str] = None,
    entity_name: Optional[str] = None
) -> Dict[str, Any]:
    """
    Infer entity schema from captured network traffic using Gemini.
    
    Args:
        samples: List of JSON samples (request/response bodies) for the entity
        ui_hints: Optional natural language description of UI fields
        entity_name: Optional entity name (e.g., "Task", "Project")
        
    Returns:
        Dictionary with inferred schema:
        {
            "entity_name": str,
            "fields": [
                {
                    "name": str,
                    "type": str,  # "string", "integer", "boolean", "datetime", "enum", etc.
                    "required": bool,
                    "constraints": dict,  # e.g., {"max_length": 255, "allowed_values": [...]}
                    "description": str
                }
            ],
            "relationships": [
                {
                    "field": str,
                    "related_entity": str,
                    "relationship_type": str  # "belongs_to", "has_many", etc.
                }
            ]
        }
    """
    if not is_ai_enabled():
        logger.warning("AI not enabled, using fallback schema inference")
        return _fallback_schema_inference(samples, entity_name)
    
    client = get_client()
    if not client:
        return _fallback_schema_inference(samples, entity_name)
    
    # Prepare samples for prompt (limit to avoid token limits)
    sample_str = json.dumps(samples[:10], indent=2)  # Limit to 10 samples
    
    # Build prompt
    prompt = f"""You are analyzing network traffic to reverse-engineer a backend API schema.

I have captured JSON samples from network requests/responses for an entity called "{entity_name or 'Entity'}".

Here are representative JSON samples:
{sample_str}
"""
    
    if ui_hints:
        prompt += f"""

Additional context from the UI:
{ui_hints}
"""
    
    prompt += """

Please analyze these samples and infer the entity schema. For each field, determine:
1. Field name
2. Data type (string, integer, boolean, datetime, enum, array, object, etc.)
3. Whether it's required or optional
4. Any constraints (max length, allowed values, format, etc.)
5. Brief description of what the field represents

Also identify any relationships to other entities (foreign keys, references).

Return a JSON object with this structure:
{
    "entity_name": "EntityName",
    "fields": [
        {
            "name": "field_name",
            "type": "string|integer|boolean|datetime|enum|array|object",
            "required": true|false,
            "constraints": {
                "max_length": 255,
                "allowed_values": ["value1", "value2"],
                "format": "email|url|date-time"
            },
            "description": "Field description"
        }
    ],
    "relationships": [
        {
            "field": "field_name",
            "related_entity": "RelatedEntity",
            "relationship_type": "belongs_to|has_many|has_one"
        }
    ]
}
"""
    
    schema_description = """{
    "entity_name": "string",
    "fields": [
        {
            "name": "string",
            "type": "string",
            "required": "boolean",
            "constraints": "object",
            "description": "string"
        }
    ],
    "relationships": [
        {
            "field": "string",
            "related_entity": "string",
            "relationship_type": "string"
        }
    ]
}"""
    
    try:
        result = client.structured_call(prompt, schema_description)
        logger.info(f"Inferred schema for {result.get('entity_name', entity_name)} using Gemini")
        return result
    except Exception as e:
        logger.error(f"Error inferring schema with Gemini: {e}")
        logger.info("Falling back to heuristic inference")
        return _fallback_schema_inference(samples, entity_name)


def _fallback_schema_inference(
    samples: List[Dict[str, Any]],
    entity_name: Optional[str] = None
) -> Dict[str, Any]:
    """
    Fallback heuristic schema inference when AI is not available.
    
    Args:
        samples: List of JSON samples
        entity_name: Optional entity name
        
    Returns:
        Inferred schema dictionary
    """
    if not samples:
        return {
            "entity_name": entity_name or "Unknown",
            "fields": [],
            "relationships": []
        }
    
    # Collect all unique fields across samples
    all_fields = set()
    for sample in samples:
        if isinstance(sample, dict):
            all_fields.update(sample.keys())
    
    fields = []
    for field_name in sorted(all_fields):
        # Analyze field across samples
        field_values = [s.get(field_name) for s in samples if isinstance(s, dict) and field_name in s]
        non_null_values = [v for v in field_values if v is not None]
        
        # Infer type
        field_type = _infer_type(field_values)
        
        # Check if required (present in all samples)
        required = len(non_null_values) == len(samples)
        
        # Infer constraints
        constraints = {}
        if field_type == "string" and non_null_values:
            max_length = max(len(str(v)) for v in non_null_values if isinstance(v, str))
            if max_length > 0:
                constraints["max_length"] = max_length
        
        fields.append({
            "name": field_name,
            "type": field_type,
            "required": required,
            "constraints": constraints,
            "description": f"Inferred from samples"
        })
    
    # Simple relationship detection (fields ending in _id)
    relationships = []
    for field in fields:
        if field["name"].endswith("_id") and field["type"] in ["string", "integer"]:
            related_entity = field["name"].replace("_id", "").title()
            relationships.append({
                "field": field["name"],
                "related_entity": related_entity,
                "relationship_type": "belongs_to"
            })
    
    return {
        "entity_name": entity_name or "Unknown",
        "fields": fields,
        "relationships": relationships
    }


def _infer_type(values: List[Any]) -> str:
    """Infer JSON schema type from a list of values."""
    if not values:
        return "string"
    
    non_null = [v for v in values if v is not None]
    if not non_null:
        return "string"
    
    # Check for consistent types
    types = set(type(v).__name__ for v in non_null)
    
    if len(types) == 1:
        type_name = types.pop()
        type_map = {
            "str": "string",
            "int": "integer",
            "float": "number",
            "bool": "boolean",
            "list": "array",
            "dict": "object"
        }
        return type_map.get(type_name, "string")
    
    # Mixed types - default to string
    return "string"

