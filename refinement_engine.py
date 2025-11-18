"""
Refinement Engine
Analyzes differences between expected specs (from captured data) and actual clone responses.
Uses AI (Gemini) when available to infer refinement rules.
"""

import json
import logging
from typing import Dict, Any, List
from deepdiff import DeepDiff

logger = logging.getLogger(__name__)

# Try to import AI agents (optional)
try:
    from ai.rule_refinement_agent import infer_rules_from_internal_diffs
    AI_AVAILABLE = True
except ImportError:
    AI_AVAILABLE = False
    logger.info("AI agents not available, using heuristic rule inference")


class RefinementEngine:
    """Analyze differences between expected behavior and actual clone responses."""
    
    def __init__(self):
        self.suggestions: List[Dict[str, Any]] = []
    
    def analyze_differences(
        self, 
        expected_responses: Dict[str, Dict[str, Any]], 
        actual_responses: Dict[str, Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Analyze differences between expected and actual responses.
        
        Args:
            expected_responses: Dict mapping endpoint names to expected response schemas/data
            actual_responses: Dict mapping endpoint names to actual clone responses
        """
        suggestions = []
        
        for endpoint_name, expected in expected_responses.items():
            actual = actual_responses.get(endpoint_name, {})
            
            if not actual:
                suggestions.append({
                    "endpoint": endpoint_name,
                    "issues": [{"type": "missing_response", "message": "No response from clone"}],
                    "fixes": [{"action": "implement_endpoint", "endpoint": endpoint_name}]
                })
                continue
            
            # Compare expected vs actual
            differences = self._compare_responses(expected, actual)
            if differences:
                suggestion = self._analyze_single_result(endpoint_name, differences, expected, actual)
                if suggestion:
                    suggestions.append(suggestion)
        
        return suggestions
    
    def _compare_responses(
        self, 
        expected: Dict[str, Any], 
        actual: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Compare expected and actual responses, return differences."""
        # Normalize both responses
        expected_norm = self._normalize_response(expected)
        actual_norm = self._normalize_response(actual)
        
        diff = DeepDiff(expected_norm, actual_norm, ignore_order=True, verbose_level=0)
        return diff.to_dict() if diff else {}
    
    def _normalize_response(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize response for comparison (remove timestamps, IDs, etc.)."""
        if not isinstance(response, dict):
            return response
        
        normalized = {}
        for key, value in response.items():
            # Skip volatile fields
            if key in ['created_at', 'updated_at', 'modified_at', 'timestamp', 'id', 'gid', '__creationTime', '__modificationTime']:
                continue
            
            # Recursively normalize nested structures
            if isinstance(value, dict):
                normalized[key] = self._normalize_response(value)
            elif isinstance(value, list):
                normalized[key] = [
                    self._normalize_response(item) if isinstance(item, dict) else item
                    for item in value
                ]
            else:
                normalized[key] = value
        
        return normalized
    
    def _analyze_single_result(
        self, 
        endpoint: str, 
        differences: Dict[str, Any],
        expected: Dict[str, Any],
        actual: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Analyze a single comparison result and suggest fixes."""
        # Try AI-powered rule inference first
        if AI_AVAILABLE:
            try:
                ai_patches = infer_rules_from_internal_diffs(
                    diff_report=differences,
                    expected_spec=expected,
                    actual_response=actual,
                    endpoint_name=endpoint
                )
                
                if ai_patches:
                    logger.info(f"AI generated {len(ai_patches)} patch suggestions for {endpoint}")
                    # Convert AI patches to our format
                    suggestions = {
                        "endpoint": endpoint,
                        "issues": [],
                        "fixes": []
                    }
                    
                    for patch in ai_patches:
                        action = patch.get("action", "")
                        field = patch.get("field", "")
                        reason = patch.get("reason", "")
                        
                        suggestions["issues"].append({
                            "type": action,
                            "field": field,
                            "reason": reason
                        })
                        suggestions["fixes"].append(patch)
                    
                    return suggestions
            except Exception as e:
                logger.warning(f"AI rule inference failed for {endpoint}: {e}, falling back to heuristics")
        
        # Fallback to heuristic analysis
        suggestions = {
            "endpoint": endpoint,
            "issues": [],
            "fixes": []
        }
        
        # Analyze missing fields
        if "dictionary_item_added" in differences:
            for field_path, value in differences["dictionary_item_added"].items():
                suggestions["issues"].append({
                    "type": "missing_field",
                    "field": field_path,
                    "expected_value": value
                })
                suggestions["fixes"].append({
                    "action": "add_field",
                    "field": field_path,
                    "value": value
                })
        
        # Analyze extra fields
        if "dictionary_item_removed" in differences:
            for field_path in differences["dictionary_item_removed"]:
                suggestions["issues"].append({
                    "type": "extra_field",
                    "field": field_path
                })
                suggestions["fixes"].append({
                    "action": "remove_field",
                    "field": field_path
                })
        
        # Analyze value mismatches
        if "values_changed" in differences:
            for field_path, change in differences["values_changed"].items():
                suggestions["issues"].append({
                    "type": "value_mismatch",
                    "field": field_path,
                    "expected": change.get("new_value"),
                    "actual": change.get("old_value")
                })
                suggestions["fixes"].append({
                    "action": "update_field",
                    "field": field_path,
                    "value": change.get("new_value")
                })
        
        # Analyze type mismatches
        if "type_changes" in differences:
            for field_path, change in differences["type_changes"].items():
                suggestions["issues"].append({
                    "type": "type_mismatch",
                    "field": field_path,
                    "expected_type": change.get("new_type"),
                    "actual_type": change.get("old_type")
                })
                suggestions["fixes"].append({
                    "action": "fix_type",
                    "field": field_path,
                    "type": change.get("new_type")
                })
        
        return suggestions if suggestions["issues"] else None
    
    def generate_schema_patches(self, suggestions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate schema patches based on suggestions."""
        patches = {
            "openapi_changes": [],
            "database_changes": [],
            "code_changes": []
        }
        
        for suggestion in suggestions:
            endpoint = suggestion.get("endpoint", "")
            
            for fix in suggestion.get("fixes", []):
                action = fix.get("action")
                field = fix.get("field")
                
                if action == "add_field":
                    patches["openapi_changes"].append({
                        "endpoint": endpoint,
                        "action": "add_property",
                        "field": field,
                        "type": self._infer_type(fix.get("value"))
                    })
                
                elif action == "remove_field":
                    patches["openapi_changes"].append({
                        "endpoint": endpoint,
                        "action": "remove_property",
                        "field": field
                    })
                
                elif action == "fix_type":
                    patches["openapi_changes"].append({
                        "endpoint": endpoint,
                        "action": "update_property_type",
                        "field": field,
                        "type": fix.get("type")
                    })
        
        return patches
    
    def _infer_type(self, value: Any) -> str:
        """Infer JSON schema type from value."""
        if isinstance(value, bool):
            return "boolean"
        elif isinstance(value, int):
            return "integer"
        elif isinstance(value, float):
            return "number"
        elif isinstance(value, list):
            return "array"
        elif isinstance(value, dict):
            return "object"
        else:
            return "string"
    
    def apply_patches(self, patches: Dict[str, Any], parsed_data: Dict[str, Any]) -> Dict[str, Any]:
        """Apply patches to parsed data structure."""
        updated_data = json.loads(json.dumps(parsed_data))  # Deep copy
        
        for change in patches.get("openapi_changes", []):
            endpoint = change.get("endpoint", "")
            action = change.get("action")
            field = change.get("field")
            
            # Find endpoint in parsed_data
            for endpoint_key, endpoint_info in updated_data.get("endpoints", {}).items():
                if endpoint in endpoint_key:
                    # Apply change to response schema
                    responses = endpoint_info.get("responses", {})
                    for status, schema in responses.items():
                        if isinstance(schema, dict) and "properties" in schema:
                            if action == "add_property":
                                schema["properties"][field] = {
                                    "type": change.get("type", "string")
                                }
                            elif action == "remove_property":
                                schema["properties"].pop(field, None)
                            elif action == "update_property_type":
                                if field in schema["properties"]:
                                    schema["properties"][field]["type"] = change.get("type")
        
        return updated_data
    
    def extract_expected_from_capture(
        self, 
        parsed_data: Dict[str, Any]
    ) -> Dict[str, Dict[str, Any]]:
        """
        Extract expected response schemas from parsed network capture data.
        This serves as the 'golden spec' for comparison.
        """
        expected = {}
        
        for endpoint_key, endpoint_info in parsed_data.get("endpoints", {}).items():
            # Extract response schemas as expected behavior
            responses = endpoint_info.get("responses", {})
            if responses:
                # Handle both list and dict formats
                if isinstance(responses, list):
                    # If responses is a list, get the first response body
                    if responses and isinstance(responses[0], dict):
                        expected[endpoint_key] = responses[0].get("body", {})
                elif isinstance(responses, dict):
                    # If responses is a dict (keyed by status code), get the first one
                    if responses:
                        first_response = list(responses.values())[0]
                        if isinstance(first_response, dict):
                            expected[endpoint_key] = first_response.get("body", first_response)
                        else:
                            expected[endpoint_key] = first_response
        
        return expected
