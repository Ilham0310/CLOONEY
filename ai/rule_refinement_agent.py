"""
Rule Refinement Agent
Uses Gemini to interpret internal diffs (expected vs actual) and generate patch suggestions.
"""

import json
import logging
from typing import Dict, Any, List, Optional
from .gemini_client import get_client, is_ai_enabled

logger = logging.getLogger(__name__)


def infer_rules_from_internal_diffs(
    diff_report: Dict[str, Any],
    expected_spec: Dict[str, Any],
    actual_response: Dict[str, Any],
    endpoint_name: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Infer refinement rules from internal diffs using Gemini.
    
    Args:
        diff_report: Pre-computed diff between expected and actual (from DeepDiff or similar)
        expected_spec: Expected response schema or sample
        actual_response: Actual response from generated backend
        endpoint_name: Optional endpoint name for context
        
    Returns:
        List of structured patch instructions:
        [
            {
                "target": "TaskCreateSchema|TaskResponseSchema|endpoint_validation",
                "action": "add_required_field|remove_field|update_field_type|add_validation|set_default",
                "field": "field_name",
                "value": {...},  # New value, default value, or constraint
                "reason": "Human-readable explanation"
            }
        ]
    """
    if not is_ai_enabled():
        logger.warning("AI not enabled, using fallback rule inference")
        return _fallback_rule_inference(diff_report, expected_spec, actual_response)
    
    client = get_client()
    if not client:
        return _fallback_rule_inference(diff_report, expected_spec, actual_response)
    
    # Prepare diff summary for prompt
    diff_summary = json.dumps(diff_report, indent=2, default=str)
    expected_str = json.dumps(expected_spec, indent=2, default=str)
    actual_str = json.dumps(actual_response, indent=2, default=str)
    
    # Build prompt
    prompt = f"""You are analyzing differences between expected and actual backend behavior to generate refinement rules.

Endpoint: {endpoint_name or "Unknown"}

Expected Response Schema/Sample:
{expected_str}

Actual Response from Generated Backend:
{actual_str}

Computed Differences:
{diff_summary}

Please analyze these differences and generate structured patch instructions to align the backend implementation with the expected behavior.

For each difference, suggest a patch instruction with:
- target: What to modify (e.g., "TaskCreateSchema", "TaskResponseSchema", "endpoint_validation")
- action: What action to take (e.g., "add_required_field", "remove_field", "update_field_type", "add_validation", "set_default")
- field: Field name (if applicable)
- value: New value, default value, or constraint (if applicable)
- reason: Brief explanation of why this change is needed

Return a JSON array of patch instructions:
[
    {{
        "target": "string",
        "action": "string",
        "field": "string",
        "value": "any",
        "reason": "string"
    }}
]
"""
    
    schema_description = """[
    {
        "target": "string",
        "action": "string",
        "field": "string",
        "value": "any",
        "reason": "string"
    }
]"""
    
    try:
        result = client.structured_call(prompt, schema_description)
        if isinstance(result, list):
            patches = result
        elif isinstance(result, dict) and "patches" in result:
            patches = result["patches"]
        else:
            patches = [result] if result else []
        
        logger.info(f"Generated {len(patches)} patch suggestions using Gemini for {endpoint_name}")
        return patches
    except Exception as e:
        logger.error(f"Error inferring rules with Gemini: {e}")
        logger.info("Falling back to heuristic rule inference")
        return _fallback_rule_inference(diff_report, expected_spec, actual_response)


def _fallback_rule_inference(
    diff_report: Dict[str, Any],
    expected_spec: Dict[str, Any],
    actual_response: Dict[str, Any]
) -> List[Dict[str, Any]]:
    """
    Fallback heuristic rule inference when AI is not available.
    
    Args:
        diff_report: Pre-computed diff
        expected_spec: Expected response
        actual_response: Actual response
        
    Returns:
        List of patch instructions
    """
    patches = []
    
    # Analyze differences
    if isinstance(diff_report, dict):
        # Missing fields in actual
        if "dictionary_item_added" in diff_report:
            for field_path, value in diff_report["dictionary_item_added"].items():
                field_name = field_path.split("'")[-2] if "'" in field_path else field_path.split(".")[-1]
                patches.append({
                    "target": "ResponseSchema",
                    "action": "add_field",
                    "field": field_name,
                    "value": value,
                    "reason": f"Field {field_name} is expected but missing in actual response"
                })
        
        # Extra fields in actual
        if "dictionary_item_removed" in diff_report:
            for field_path in diff_report["dictionary_item_removed"]:
                field_name = field_path.split("'")[-2] if "'" in field_path else field_path.split(".")[-1]
                patches.append({
                    "target": "ResponseSchema",
                    "action": "remove_field",
                    "field": field_name,
                    "value": None,
                    "reason": f"Field {field_name} is present in actual but not expected"
                })
        
        # Value mismatches
        if "values_changed" in diff_report:
            for field_path, change in diff_report["values_changed"].items():
                field_name = field_path.split("'")[-2] if "'" in field_path else field_path.split(".")[-1]
                expected_value = change.get("new_value")
                patches.append({
                    "target": "ResponseSchema",
                    "action": "update_field_value",
                    "field": field_name,
                    "value": expected_value,
                    "reason": f"Field {field_name} has different value than expected"
                })
        
        # Type mismatches
        if "type_changes" in diff_report:
            for field_path, change in diff_report["type_changes"].items():
                field_name = field_path.split("'")[-2] if "'" in field_path else field_path.split(".")[-1]
                expected_type = change.get("new_type", {}).__name__ if hasattr(change.get("new_type"), "__name__") else str(change.get("new_type"))
                patches.append({
                    "target": "ResponseSchema",
                    "action": "update_field_type",
                    "field": field_name,
                    "value": expected_type,
                    "reason": f"Field {field_name} has different type than expected"
                })
    
    return patches

