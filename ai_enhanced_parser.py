"""
AI-Enhanced Network Parser
Wraps NetworkParser with AI-powered schema and endpoint inference.
"""

import json
import logging
from typing import Dict, Any, List, Optional
from network_parser import NetworkParser

logger = logging.getLogger(__name__)

# Try to import AI agents (optional)
try:
    from ai.schema_inference_agent import infer_schema_with_gemini
    from ai.endpoint_inference_agent import infer_endpoint_spec_with_gemini
    from ai.gemini_client import is_ai_enabled
    AI_AVAILABLE = True
except ImportError:
    AI_AVAILABLE = False
    logger.info("AI agents not available, using standard network parser")


class AIEnhancedParser(NetworkParser):
    """Network parser with optional AI-powered schema and endpoint inference."""
    
    def __init__(self, network_capture_path: str, use_ai: Optional[bool] = None):
        """
        Initialize AI-enhanced parser.
        
        Args:
            network_capture_path: Path to network capture JSON file
            use_ai: Whether to use AI (defaults to checking if AI is enabled)
        """
        super().__init__(network_capture_path)
        self.use_ai = use_ai if use_ai is not None else (AI_AVAILABLE and is_ai_enabled())
        
        if self.use_ai:
            logger.info("AI-enhanced parsing enabled")
        else:
            logger.info("Using standard heuristic parsing")
    
    def infer_schemas(self) -> Dict[str, Dict[str, Any]]:
        """Infer schemas with optional AI enhancement."""
        if not self.use_ai:
            # Fall back to standard inference
            return super().infer_schemas()
        
        logger.info("Using AI to infer schemas...")
        enhanced_schemas = {}
        
        # Group endpoints by entity for better AI inference
        entity_groups = self._group_endpoints_by_entity()
        
        for entity_name, endpoints in entity_groups.items():
            # Collect samples for this entity
            samples = []
            for endpoint_key in endpoints:
                endpoint_info = self.endpoints.get(endpoint_key, {})
                # Collect response samples
                for resp in endpoint_info.get('responses', []):
                    if resp.get('body'):
                        samples.append(resp['body'])
                # Collect request samples
                for req in endpoint_info.get('requests', []):
                    if req:
                        samples.append(req)
            
            if samples:
                try:
                    # Use AI to infer schema
                    ai_schema = infer_schema_with_gemini(
                        samples=samples[:20],  # Limit samples
                        entity_name=entity_name
                    )
                    
                    # Apply AI-inferred schema to relevant endpoints
                    for endpoint_key in endpoints:
                        endpoint_info = self.endpoints.get(endpoint_key, {})
                        if endpoint_key not in enhanced_schemas:
                            enhanced_schemas[endpoint_key] = {
                                'requests': {},
                                'responses': {}
                            }
                        
                        # Map AI schema to endpoint schemas
                        # This is a simplified mapping - could be enhanced
                        if ai_schema.get('fields'):
                            # Create response schema from AI-inferred fields
                            properties = {}
                            required = []
                            for field in ai_schema['fields']:
                                field_name = field['name']
                                field_type = field['type']
                                properties[field_name] = {
                                    'type': field_type,
                                    **field.get('constraints', {})
                                }
                                if field.get('required'):
                                    required.append(field_name)
                            
                            response_schema = {
                                'type': 'object',
                                'properties': properties
                            }
                            if required:
                                response_schema['required'] = required
                            
                            # Use first status code or default to 200
                            status = 200
                            if endpoint_info.get('responses'):
                                status = endpoint_info['responses'][0].get('status', 200)
                            
                            enhanced_schemas[endpoint_key]['responses'][str(status)] = response_schema
                    
                    logger.info(f"AI inferred schema for {entity_name} with {len(ai_schema.get('fields', []))} fields")
                except Exception as e:
                    logger.warning(f"AI schema inference failed for {entity_name}: {e}, using heuristics")
                    # Fall back to standard inference for this entity
                    for endpoint_key in endpoints:
                        if endpoint_key not in enhanced_schemas:
                            standard_schemas = super().infer_schemas()
                            if endpoint_key in standard_schemas:
                                enhanced_schemas[endpoint_key] = standard_schemas[endpoint_key]
        
        # Fill in any endpoints not covered by AI
        standard_schemas = super().infer_schemas()
        for endpoint_key, schema_info in standard_schemas.items():
            if endpoint_key not in enhanced_schemas:
                enhanced_schemas[endpoint_key] = schema_info
        
        return enhanced_schemas
    
    def _group_endpoints_by_entity(self) -> Dict[str, List[str]]:
        """Group endpoints by inferred entity name."""
        entity_groups = {}
        
        for endpoint_key in self.endpoints.keys():
            # Extract entity name from endpoint path
            # e.g., "POST /api/1.0/tasks" -> "Task"
            parts = endpoint_key.split()
            if len(parts) >= 2:
                path = parts[1]
                # Extract entity from path (e.g., /api/1.0/tasks -> Task)
                path_parts = [p for p in path.split('/') if p and p != 'api' and not p.replace('.', '').isdigit()]
                if path_parts:
                    entity_name = path_parts[-1].rstrip('s').title()  # Remove plural, title case
                    if entity_name not in entity_groups:
                        entity_groups[entity_name] = []
                    entity_groups[entity_name].append(endpoint_key)
        
        return entity_groups
    
    def analyze(self) -> Dict[str, Any]:
        """Run full analysis with optional AI enhancement."""
        print("Extracting endpoints...")
        endpoints = self.extract_endpoints()
        print(f"Found {len(endpoints)} distinct endpoints")
        
        print("Inferring schemas...")
        if self.use_ai:
            print("  Using AI-powered inference...")
        schemas = self.infer_schemas()
        print(f"Inferred schemas for {len(schemas)} endpoints")
        
        print("Detecting relationships...")
        relationships = self.get_entity_relationships()
        print(f"Found relationships: {relationships}")
        
        # Optionally enhance endpoints with AI
        if self.use_ai:
            print("Enhancing endpoints with AI inference...")
            enhanced_endpoints = self._enhance_endpoints_with_ai(endpoints)
            endpoints = enhanced_endpoints
        
        return {
            'endpoints': endpoints,
            'schemas': schemas,
            'relationships': relationships
        }
    
    def _enhance_endpoints_with_ai(self, endpoints: Dict[str, Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
        """Enhance endpoint definitions with AI inference."""
        enhanced = {}
        
        for endpoint_key, endpoint_info in endpoints.items():
            # Group messages for this endpoint
            messages = []
            for req in endpoint_info.get('requests', []):
                messages.append({
                    'method': endpoint_key.split()[0] if ' ' in endpoint_key else 'GET',
                    'request': {'body': req},
                    'url': endpoint_key.split()[1] if ' ' in endpoint_key else ''
                })
            for resp in endpoint_info.get('responses', []):
                messages.append({
                    'method': endpoint_key.split()[0] if ' ' in endpoint_key else 'GET',
                    'response': resp,
                    'url': endpoint_key.split()[1] if ' ' in endpoint_key else ''
                })
            
            if messages:
                try:
                    # Use AI to infer endpoint spec
                    ai_spec = infer_endpoint_spec_with_gemini(
                        messages=messages[:20],  # Limit messages
                        operation_name=endpoint_key
                    )
                    
                    # Merge AI spec with existing endpoint info
                    enhanced[endpoint_key] = {
                        **endpoint_info,
                        'ai_enhanced': True,
                        'method': ai_spec.get('method', endpoint_info.get('methods', ['GET'])[0]),
                        'path': ai_spec.get('path', endpoint_key.split()[1] if ' ' in endpoint_key else ''),
                        'operation': ai_spec.get('operation'),
                        'description': ai_spec.get('description'),
                        'expected_status_codes': ai_spec.get('expected_status_codes', [200])
                    }
                    
                    logger.info(f"AI enhanced endpoint: {endpoint_key}")
                except Exception as e:
                    logger.warning(f"AI endpoint inference failed for {endpoint_key}: {e}")
                    enhanced[endpoint_key] = endpoint_info
            else:
                enhanced[endpoint_key] = endpoint_info
        
        return enhanced

