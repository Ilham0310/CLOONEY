"""
Network Traffic Parser
Extracts API endpoints, methods, and infers data schemas from network capture JSON.
"""

import json
import re
from collections import defaultdict
from typing import Dict, List, Any, Optional, Set
from urllib.parse import urlparse, parse_qs
from datetime import datetime


class NetworkParser:
    """Parse network capture JSON and extract API information."""
    
    def __init__(self, network_capture_path: str):
        self.network_capture_path = network_capture_path
        self.endpoints: Dict[str, Dict[str, Any]] = defaultdict(lambda: {
            'methods': set(),
            'requests': [],
            'responses': [],
            'query_params': set(),
            'path_params': set()
        })
        self.schemas: Dict[str, Dict[str, Any]] = {}
        
    def load_network_capture(self) -> List[Dict[str, Any]]:
        """Load network capture JSON file."""
        with open(self.network_capture_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def is_api_endpoint(self, url: str, request: Dict[str, Any] = None, response: Dict[str, Any] = None) -> bool:
        """Determine if URL is an API endpoint."""
        # Filter for Asana API endpoints
        patterns = [
            r'app\.asana\.com/api/',
            r'app\.asana\.com/-/api/',
            r'app\.asana\.com/api/1\.0/',
            r'app\.asana\.com/-/[^/]+',  # Internal API endpoints like /-/web_login_options
            r'cdp-api\.asana\.com',  # Asana CDP API
            r'graphql',
            r'/api/v1/',
        ]
        
        # Check URL patterns
        if any(re.search(pattern, url, re.IGNORECASE) for pattern in patterns):
            return True
        
        # Also consider POST/PUT/DELETE/PATCH requests with JSON content as potential API calls
        if request:
            method = request.get('method', '').upper()
            content_type = request.get('headers', {}).get('content-type', '')
            post_data = request.get('post_data')
            
            # Check if it's a mutation method with JSON
            if method in ['POST', 'PUT', 'DELETE', 'PATCH']:
                if 'application/json' in content_type.lower() or (post_data and post_data.strip().startswith('{')):
                    # Exclude tracking/analytics endpoints
                    if not any(exclude in url.lower() for exclude in ['analytics', 'tracking', 'pixel', 'doubleclick', 'google', 'spotify']):
                        return True
        
        # Check response for JSON content
        if response:
            resp_content_type = response.get('headers', {}).get('content-type', '')
            if 'application/json' in resp_content_type.lower():
                # Exclude tracking/analytics
                if not any(exclude in url.lower() for exclude in ['analytics', 'tracking', 'pixel', 'doubleclick', 'google', 'spotify']):
                    # Include if it's to app.asana.com
                    if 'app.asana.com' in url or 'asana.com' in url:
                        return True
        
        return False
    
    def normalize_url(self, url: str) -> tuple:
        """Normalize URL by extracting path and parameters."""
        parsed = urlparse(url)
        path = parsed.path
        
        # Extract query parameters
        query_params = parse_qs(parsed.query)
        
        # Replace numeric IDs and GUIDs with placeholders
        path = re.sub(r'/\d+', '/{id}', path)
        path = re.sub(r'/[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}', '/{uuid}', path, flags=re.IGNORECASE)
        path = re.sub(r'/[a-f0-9]{15,}', '/{gid}', path, flags=re.IGNORECASE)
        
        return path, query_params
    
    def extract_path_params(self, original_path: str, normalized_path: str) -> Set[str]:
        """Extract path parameter names from normalized path."""
        params = re.findall(r'\{(\w+)\}', normalized_path)
        return set(params)
    
    def parse_json_body(self, body: str) -> Optional[Dict[str, Any]]:
        """Parse JSON body, handling various formats."""
        if not body or body == 'null':
            return None
        
        # Handle base64 encoded content
        if body.startswith('[BINARY_CONTENT_BASE64]:'):
            return None
        
        try:
            # Try parsing as JSON
            return json.loads(body)
        except (json.JSONDecodeError, TypeError):
            # Try extracting JSON from HTML/other content
            json_match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', body, re.DOTALL)
            if json_match:
                try:
                    return json.loads(json_match.group(0))
                except json.JSONDecodeError:
                    pass
            return None
    
    def infer_schema_from_data(self, data: Any, path: str = '') -> Dict[str, Any]:
        """Infer schema from data structure."""
        if data is None:
            return {'type': 'null'}
        
        if isinstance(data, bool):
            return {'type': 'boolean'}
        
        if isinstance(data, int):
            return {'type': 'integer'}
        
        if isinstance(data, float):
            return {'type': 'number'}
        
        if isinstance(data, str):
            # Try to infer format
            if re.match(r'^\d{4}-\d{2}-\d{2}', data):
                return {'type': 'string', 'format': 'date'}
            if re.match(r'^\d{4}-\d{2}-\d{2}T', data):
                return {'type': 'string', 'format': 'date-time'}
            if re.match(r'^[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}$', data, re.IGNORECASE):
                return {'type': 'string', 'format': 'uuid'}
            if data.startswith('http://') or data.startswith('https://'):
                return {'type': 'string', 'format': 'uri'}
            return {'type': 'string'}
        
        if isinstance(data, list):
            if len(data) == 0:
                return {'type': 'array', 'items': {}}
            # Infer schema from first item
            item_schema = self.infer_schema_from_data(data[0], f'{path}[]')
            return {'type': 'array', 'items': item_schema}
        
        if isinstance(data, dict):
            properties = {}
            required = []
            
            for key, value in data.items():
                prop_schema = self.infer_schema_from_data(value, f'{path}.{key}')
                properties[key] = prop_schema
                
                # Consider field required if it's not None and not empty string
                if value is not None and value != '':
                    required.append(key)
            
            return {
                'type': 'object',
                'properties': properties,
                'required': required if required else None
            }
        
        return {'type': 'string'}  # Default fallback
    
    def merge_schemas(self, schema1: Dict[str, Any], schema2: Dict[str, Any]) -> Dict[str, Any]:
        """Merge two schemas, handling conflicts."""
        if schema1.get('type') != schema2.get('type'):
            # Type conflict - use union or most specific
            if schema1.get('type') == 'null':
                return schema2
            if schema2.get('type') == 'null':
                return schema1
            # Keep both types
            return {'anyOf': [schema1, schema2]}
        
        if schema1.get('type') == 'object':
            properties = {}
            required = set()
            
            # Merge properties
            all_keys = set(schema1.get('properties', {}).keys()) | set(schema2.get('properties', {}).keys())
            for key in all_keys:
                prop1 = schema1.get('properties', {}).get(key, {})
                prop2 = schema2.get('properties', {}).get(key, {})
                
                if prop1 and prop2:
                    properties[key] = self.merge_schemas(prop1, prop2)
                else:
                    properties[key] = prop1 or prop2
                
                # Field is required if it appears in either schema's required list
                if key in schema1.get('required', []) or key in schema2.get('required', []):
                    required.add(key)
            
            result = {
                'type': 'object',
                'properties': properties
            }
            if required:
                result['required'] = sorted(list(required))
            return result
        
        if schema1.get('type') == 'array':
            items1 = schema1.get('items', {})
            items2 = schema2.get('items', {})
            return {
                'type': 'array',
                'items': self.merge_schemas(items1, items2) if items1 and items2 else (items1 or items2)
            }
        
        # For primitive types, prefer more specific format
        return schema1 if schema1.get('format') else schema2
    
    def extract_endpoints(self) -> Dict[str, Dict[str, Any]]:
        """Extract all distinct API endpoints from network capture."""
        network_logs = self.load_network_capture()
        
        for entry in network_logs:
            request = entry.get('request', {})
            response = entry.get('response', {})
            
            url = request.get('url', '')
            method = request.get('method', 'GET')
            
            if not self.is_api_endpoint(url, request, response):
                continue
            
            normalized_path, query_params = self.normalize_url(url)
            path_params = self.extract_path_params(url, normalized_path)
            
            endpoint_key = f"{method} {normalized_path}"
            endpoint_info = self.endpoints[endpoint_key]
            
            endpoint_info['methods'].add(method)
            endpoint_info['path_params'].update(path_params)
            endpoint_info['query_params'].update(query_params.keys())
            
            # Parse request body
            post_data = request.get('post_data')
            request_body = None
            if post_data:
                request_body = self.parse_json_body(post_data)
            
            # Parse response body
            response_body_str = response.get('body', '') if response else ''
            response_body = None
            if response_body_str:
                response_body = self.parse_json_body(response_body_str)
            
            # Store request/response samples
            if request_body:
                endpoint_info['requests'].append(request_body)
            if response_body:
                endpoint_info['responses'].append({
                    'status': response.get('status'),
                    'body': response_body
                })
        
        # Convert sets to lists for JSON serialization
        result = {}
        for key, info in self.endpoints.items():
            result[key] = {
                'methods': list(info['methods']),
                'requests': info['requests'],
                'responses': info['responses'],
                'query_params': list(info['query_params']),
                'path_params': list(info['path_params'])
            }
        
        return result
    
    def infer_schemas(self) -> Dict[str, Dict[str, Any]]:
        """Infer schemas for all endpoints."""
        for endpoint_key, endpoint_info in self.endpoints.items():
            request_schemas = []
            response_schemas = []
            
            # Infer request schema from all request samples
            for req in endpoint_info['requests']:
                schema = self.infer_schema_from_data(req)
                request_schemas.append(schema)
            
            # Infer response schema from all response samples
            for resp in endpoint_info['responses']:
                if resp.get('body'):
                    schema = self.infer_schema_from_data(resp['body'])
                    response_schemas.append(schema)
            
            # Merge all request schemas
            merged_request = {}
            if request_schemas:
                merged_request = request_schemas[0]
                for schema in request_schemas[1:]:
                    merged_request = self.merge_schemas(merged_request, schema)
            
            # Merge all response schemas (grouped by status code)
            merged_responses = {}
            status_groups = defaultdict(list)
            for resp in endpoint_info['responses']:
                status = resp.get('status', 200)
                if resp.get('body'):
                    status_groups[status].append(self.infer_schema_from_data(resp['body']))
            
            for status, schemas in status_groups.items():
                if schemas:
                    merged = schemas[0]
                    for schema in schemas[1:]:
                        merged = self.merge_schemas(merged, schema)
                    merged_responses[status] = merged
            
            self.schemas[endpoint_key] = {
                'request': merged_request,
                'responses': merged_responses,
                'path_params': list(endpoint_info['path_params']),
                'query_params': list(endpoint_info['query_params'])
            }
        
        return self.schemas
    
    def get_entity_relationships(self) -> Dict[str, List[str]]:
        """Detect relationships between entities from schemas."""
        relationships = defaultdict(list)
        
        for endpoint_key, schema_info in self.schemas.items():
            # Look for common entity patterns in paths
            path = endpoint_key.split(' ', 1)[1] if ' ' in endpoint_key else endpoint_key
            
            # Extract entity names from paths
            entities = re.findall(r'/(\w+)', path)
            
            # Look for foreign key patterns in schemas
            request_schema = schema_info.get('request', {})
            response_schemas = schema_info.get('responses', {})
            
            all_schemas = [request_schema] + list(response_schemas.values())
            
            for schema in all_schemas:
                if schema.get('type') == 'object':
                    props = schema.get('properties', {})
                    for prop_name, prop_schema in props.items():
                        # Look for ID fields
                        if 'id' in prop_name.lower() or 'gid' in prop_name.lower():
                            # Try to infer related entity
                            entity_name = prop_name.replace('_id', '').replace('Id', '').replace('gid', '')
                            if entity_name and entities:
                                relationships[entity_name].extend(entities)
        
        return dict(relationships)
    
    def analyze(self) -> Dict[str, Any]:
        """Run full analysis and return results."""
        print("Extracting endpoints...")
        endpoints = self.extract_endpoints()
        print(f"Found {len(endpoints)} distinct endpoints")
        
        print("Inferring schemas...")
        schemas = self.infer_schemas()
        print(f"Inferred schemas for {len(schemas)} endpoints")
        
        print("Detecting relationships...")
        relationships = self.get_entity_relationships()
        print(f"Found relationships: {relationships}")
        
        return {
            'endpoints': endpoints,
            'schemas': schemas,
            'relationships': relationships
        }


if __name__ == '__main__':
    parser = NetworkParser('network_capture.json')
    results = parser.analyze()
    
    # Save results
    with open('parsed_endpoints.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\nAnalysis complete! Results saved to parsed_endpoints.json")

