"""
OpenAPI Specification Generator
Generates OpenAPI 3.0 specification from parsed network data.
"""

import json
from typing import Dict, Any, List
from datetime import datetime


class OpenAPIGenerator:
    """Generate OpenAPI specification from parsed endpoints and schemas."""
    
    def __init__(self, parsed_data: Dict[str, Any]):
        self.parsed_data = parsed_data
        self.endpoints = parsed_data.get('endpoints', {})
        self.schemas = parsed_data.get('schemas', {})
        self.relationships = parsed_data.get('relationships', {})
    
    def convert_json_schema_to_openapi(self, schema: Dict[str, Any]) -> Dict[str, Any]:
        """Convert inferred JSON schema to OpenAPI schema format."""
        if not schema:
            return {}
        
        # Handle type unions
        if 'anyOf' in schema:
            return {'oneOf': [self.convert_json_schema_to_openapi(s) for s in schema['anyOf']]}
        
        result = {}
        
        if 'type' in schema:
            result['type'] = schema['type']
        
        if 'format' in schema:
            result['format'] = schema['format']
        
        if schema.get('type') == 'object':
            if 'properties' in schema:
                result['properties'] = {
                    k: self.convert_json_schema_to_openapi(v)
                    for k, v in schema['properties'].items()
                }
            
            if 'required' in schema and schema['required']:
                result['required'] = schema['required']
        
        elif schema.get('type') == 'array':
            if 'items' in schema:
                result['items'] = self.convert_json_schema_to_openapi(schema['items'])
        
        return result
    
    def generate_path_item(self, endpoint_key: str, endpoint_info: Dict[str, Any], schema_info: Dict[str, Any]) -> Dict[str, Any]:
        """Generate OpenAPI path item for an endpoint."""
        method, path = endpoint_key.split(' ', 1)
        method = method.lower()
        
        path_item = {
            'summary': f"{method.upper()} {path}",
            'operationId': f"{method}_{path.replace('/', '_').replace('{', '').replace('}', '').strip('_')}",
            'tags': self._extract_tags(path),
        }
        
        # Add path parameters
        path_params = schema_info.get('path_params', [])
        if path_params:
            path_item['parameters'] = [
                {
                    'name': param,
                    'in': 'path',
                    'required': True,
                    'schema': {'type': 'string'}
                }
                for param in path_params
            ]
        
        # Add query parameters
        query_params = schema_info.get('query_params', [])
        if query_params:
            if 'parameters' not in path_item:
                path_item['parameters'] = []
            path_item['parameters'].extend([
                {
                    'name': param,
                    'in': 'query',
                    'required': False,
                    'schema': {'type': 'string'}
                }
                for param in query_params
            ])
        
        # Add request body for POST, PUT, PATCH
        if method in ['post', 'put', 'patch']:
            request_schema = schema_info.get('request', {})
            if request_schema:
                path_item['requestBody'] = {
                    'required': True,
                    'content': {
                        'application/json': {
                            'schema': self.convert_json_schema_to_openapi(request_schema)
                        }
                    }
                }
        
        # Add responses
        path_item['responses'] = {}
        response_schemas = schema_info.get('responses', {})
        
        if response_schemas:
            for status, schema in response_schemas.items():
                path_item['responses'][str(status)] = {
                    'description': self._get_status_description(status),
                    'content': {
                        'application/json': {
                            'schema': self.convert_json_schema_to_openapi(schema)
                        }
                    }
                }
        else:
            # Default responses
            path_item['responses'] = {
                '200': {
                    'description': 'Success',
                    'content': {
                        'application/json': {
                            'schema': {'type': 'object'}
                        }
                    }
                },
                '400': {'description': 'Bad Request'},
                '401': {'description': 'Unauthorized'},
                '404': {'description': 'Not Found'},
                '500': {'description': 'Internal Server Error'}
            }
        
        return path_item
    
    def _extract_tags(self, path: str) -> List[str]:
        """Extract tags from path for grouping endpoints."""
        tags = []
        if '/projects' in path or '/project' in path:
            tags.append('Projects')
        elif '/tasks' in path or '/task' in path:
            tags.append('Tasks')
        elif '/sections' in path or '/section' in path:
            tags.append('Sections')
        elif '/users' in path or '/user' in path:
            tags.append('Users')
        elif '/home' in path:
            tags.append('Home')
        else:
            tags.append('General')
        return tags
    
    def _get_status_description(self, status: int) -> str:
        """Get description for HTTP status code."""
        descriptions = {
            200: 'Success',
            201: 'Created',
            204: 'No Content',
            400: 'Bad Request',
            401: 'Unauthorized',
            403: 'Forbidden',
            404: 'Not Found',
            422: 'Unprocessable Entity',
            500: 'Internal Server Error'
        }
        return descriptions.get(status, f'Status {status}')
    
    def generate(self) -> Dict[str, Any]:
        """Generate complete OpenAPI specification."""
        spec = {
            'openapi': '3.0.3',
            'info': {
                'title': 'Asana API Clone',
                'description': 'API specification inferred from network traffic analysis',
                'version': '1.0.0',
                'contact': {
                    'name': 'API Support'
                }
            },
            'servers': [
                {
                    'url': 'https://app.asana.com/api/1.0',
                    'description': 'Asana API Server'
                }
            ],
            'paths': {},
            'components': {
                'schemas': {},
                'securitySchemes': {
                    'bearerAuth': {
                        'type': 'http',
                        'scheme': 'bearer',
                        'bearerFormat': 'JWT'
                    }
                }
            },
            'security': [
                {'bearerAuth': []}
            ]
        }
        
        # Generate paths
        for endpoint_key, endpoint_info in self.endpoints.items():
            if endpoint_key not in self.schemas:
                continue
            
            method, path = endpoint_key.split(' ', 1)
            method = method.lower()
            schema_info = self.schemas[endpoint_key]
            
            if path not in spec['paths']:
                spec['paths'][path] = {}
            
            spec['paths'][path][method] = self.generate_path_item(
                endpoint_key, endpoint_info, schema_info
            )
        
        # Extract and add component schemas
        self._extract_component_schemas(spec)
        
        return spec
    
    def _extract_component_schemas(self, spec: Dict[str, Any]):
        """Extract reusable schemas from responses."""
        seen_schemas = {}
        
        for schema_info in self.schemas.values():
            for status, response_schema in schema_info.get('responses', {}).items():
                # Look for common entity schemas
                if response_schema.get('type') == 'object':
                    props = response_schema.get('properties', {})
                    
                    # Check if this looks like a standard entity
                    if 'id' in props or 'gid' in props:
                        # Try to infer entity name
                        entity_name = self._infer_entity_name(props)
                        if entity_name and entity_name not in seen_schemas:
                            seen_schemas[entity_name] = self.convert_json_schema_to_openapi(response_schema)
        
        spec['components']['schemas'] = seen_schemas
    
    def _infer_entity_name(self, properties: Dict[str, Any]) -> str:
        """Infer entity name from properties."""
        # Common patterns
        if 'name' in properties:
            return 'Entity'
        if 'title' in properties:
            return 'Entity'
        if 'project' in str(properties).lower():
            return 'Project'
        if 'task' in str(properties).lower():
            return 'Task'
        if 'section' in str(properties).lower():
            return 'Section'
        if 'user' in str(properties).lower():
            return 'User'
        return None
    
    def save(self, output_path: str = 'api.yml'):
        """Save OpenAPI specification to file."""
        spec = self.generate()
        
        # Convert to YAML
        try:
            import yaml
            with open(output_path, 'w') as f:
                yaml.dump(spec, f, default_flow_style=False, sort_keys=False)
            print(f"OpenAPI specification saved to {output_path}")
        except ImportError:
            # Fallback to JSON
            with open(output_path.replace('.yml', '.json'), 'w') as f:
                json.dump(spec, f, indent=2)
            print(f"OpenAPI specification saved to {output_path.replace('.yml', '.json')} (YAML not available)")


if __name__ == '__main__':
    # Load parsed data
    with open('parsed_endpoints.json', 'r') as f:
        parsed_data = json.load(f)
    
    generator = OpenAPIGenerator(parsed_data)
    generator.save('api.yml')

