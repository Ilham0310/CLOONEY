#!/usr/bin/env python3
"""
Convert WebSocket CRUD operations to REST API endpoints.
This creates a mapping from Asana's WebSocket sync protocol to REST API.
"""

import json
from typing import Dict, Any, List
from collections import defaultdict

def convert_websocket_to_rest(entities_file: str, crud_operations_file: str = None) -> Dict[str, Any]:
    """Convert WebSocket operations to REST API endpoints."""
    
    with open(entities_file, 'r') as f:
        entities_data = json.load(f)
    
    entity_schemas = entities_data.get('entity_schemas', {})
    entity_types = entities_data.get('entity_types', {})
    
    # Map entity types to REST endpoints
    # "Pot" in Asana is actually "Project" (Portfolio of Tasks)
    entity_to_endpoint = {
        'Task': 'tasks',
        'Pot': 'projects',  # Pot = Project in Asana
        'Column': 'sections',
        'ColumnTask': 'tasks',  # Tasks in columns
        'User': 'users',
        'Team': 'teams',
        'Domain': 'workspaces',
    }
    
    # Generate REST endpoints
    rest_endpoints = {}
    
    for entity_type, schema in entity_schemas.items():
        # Map to REST endpoint name
        endpoint_name = entity_to_endpoint.get(entity_type, entity_type.lower() + 's')
        
        operations = schema.get('operations', [])
        fields = schema.get('fields', [])
        
        # Convert WebSocket operations to HTTP methods
        if 'added' in operations:
            # POST /api/1.0/{endpoint}
            rest_endpoints[f'POST /api/1.0/{endpoint_name}'] = {
                'method': 'POST',
                'path': f'/api/1.0/{endpoint_name}',
                'entity_type': entity_type,
                'request_schema': infer_request_schema(fields, entity_type),
                'response_schema': infer_response_schema(fields, entity_type),
                'description': f'Create a new {entity_type}'
            }
        
        if 'changed' in operations:
            # PUT /api/1.0/{endpoint}/{id}
            rest_endpoints[f'PUT /api/1.0/{endpoint_name}/{{id}}'] = {
                'method': 'PUT',
                'path': f'/api/1.0/{endpoint_name}/{{id}}',
                'entity_type': entity_type,
                'request_schema': infer_request_schema(fields, entity_type, update=True),
                'response_schema': infer_response_schema(fields, entity_type),
                'description': f'Update an existing {entity_type}'
            }
        
        if 'removed' in operations or 'batch_removed' in operations:
            # DELETE /api/1.0/{endpoint}/{id}
            rest_endpoints[f'DELETE /api/1.0/{endpoint_name}/{{id}}'] = {
                'method': 'DELETE',
                'path': f'/api/1.0/{endpoint_name}/{{id}}',
                'entity_type': entity_type,
                'response_schema': {'type': 'object', 'properties': {'success': {'type': 'boolean'}}},
                'description': f'Delete a {entity_type}'
            }
        
        # GET endpoints (always available)
        rest_endpoints[f'GET /api/1.0/{endpoint_name}'] = {
            'method': 'GET',
            'path': f'/api/1.0/{endpoint_name}',
            'entity_type': entity_type,
            'response_schema': {
                'type': 'object',
                'properties': {
                    'data': {
                        'type': 'array',
                        'items': infer_response_schema(fields, entity_type)
                    }
                }
            },
            'description': f'List all {entity_type}s'
        }
        
        rest_endpoints[f'GET /api/1.0/{endpoint_name}/{{id}}'] = {
            'method': 'GET',
            'path': f'/api/1.0/{endpoint_name}/{{id}}',
            'entity_type': entity_type,
            'response_schema': infer_response_schema(fields, entity_type),
            'description': f'Get a specific {entity_type} by ID'
        }
    
    return {
        'endpoints': rest_endpoints,
        'summary': {
            'total_endpoints': len(rest_endpoints),
            'entity_types': list(entity_schemas.keys()),
            'crud_coverage': {
                'create': sum(1 for e in rest_endpoints.values() if e['method'] == 'POST'),
                'read': sum(1 for e in rest_endpoints.values() if e['method'] == 'GET'),
                'update': sum(1 for e in rest_endpoints.values() if e['method'] == 'PUT'),
                'delete': sum(1 for e in rest_endpoints.values() if e['method'] == 'DELETE'),
            }
        }
    }

def infer_request_schema(fields: List[str], entity_type: str, update: bool = False) -> Dict[str, Any]:
    """Infer request schema from fields."""
    properties = {}
    required = []
    
    # Common required fields for creation
    if not update:
        if 'name' in fields:
            required.append('name')
    
    # Map fields to types
    for field in fields:
        if field.startswith('__') or field in ['id', 'typeName', '__creationTime', '__trashedAt']:
            continue  # Skip internal fields
        
        field_type = infer_field_type(field, entity_type)
        properties[field] = field_type
        
        # Some fields might be required
        if field in ['name', 'workspace', 'project'] and not update:
            required.append(field)
    
    return {
        'type': 'object',
        'properties': properties,
        'required': required if not update else []
    }

def infer_response_schema(fields: List[str], entity_type: str) -> Dict[str, Any]:
    """Infer response schema from fields."""
    properties = {}
    
    for field in fields:
        field_type = infer_field_type(field, entity_type)
        properties[field] = field_type
    
    return {
        'type': 'object',
        'properties': properties
    }

def infer_field_type(field_name: str, entity_type: str) -> Dict[str, Any]:
    """Infer field type from field name and entity type."""
    field_lower = field_name.lower()
    
    # String fields
    if any(kw in field_lower for kw in ['name', 'title', 'description', 'notes', 'email', 'url', 'id', 'key']):
        return {'type': 'string'}
    
    # Boolean fields
    if any(kw in field_lower for kw in ['is', 'has', 'enable', 'can', 'active', 'completed', 'public', 'private']):
        return {'type': 'boolean'}
    
    # Number fields
    if any(kw in field_lower for kw in ['count', 'num', 'size', 'time', 'date', 'created', 'updated']):
        if 'time' in field_lower or 'date' in field_lower or 'created' in field_lower or 'updated' in field_lower:
            return {'type': 'string', 'format': 'date-time'}
        return {'type': 'integer'}
    
    # Array fields
    if field_lower.endswith('s') and field_lower not in ['settings', 'properties']:
        return {'type': 'array', 'items': {'type': 'object'}}
    
    # JSON fields
    if field_lower.endswith('json') or 'json' in field_lower:
        return {'type': 'object'}
    
    # Default to string
    return {'type': 'string'}

if __name__ == '__main__':
    import sys
    entities_file = sys.argv[1] if len(sys.argv) > 1 else 'websocket_entities.json'
    
    try:
        result = convert_websocket_to_rest(entities_file)
        
        print("=" * 80)
        print("WEBSOCKET TO REST API CONVERSION")
        print("=" * 80)
        print(f"\nTotal REST endpoints generated: {result['summary']['total_endpoints']}")
        print(f"\nCRUD Coverage:")
        for op, count in result['summary']['crud_coverage'].items():
            print(f"  {op.upper()}: {count} endpoints")
        
        print(f"\nGenerated Endpoints:")
        for endpoint_key, endpoint_info in sorted(result['endpoints'].items()):
            if endpoint_info['entity_type'] in ['Task', 'Pot', 'Column', 'User']:
                print(f"  {endpoint_info['method']} {endpoint_info['path']}")
                print(f"    Entity: {endpoint_info['entity_type']}")
                print(f"    Description: {endpoint_info['description']}")
        
        # Save to file
        output_file = 'rest_endpoints_from_websocket.json'
        with open(output_file, 'w') as f:
            json.dump(result, f, indent=2, default=str)
        print(f"\n✅ REST endpoints saved to {output_file}")
        
    except FileNotFoundError:
        print(f"Error: {entities_file} not found")
        print("Run extract_entities_from_websocket.py first to generate the entities file.")
    except Exception as e:
        import traceback
        print(f"Error: {e}")
        traceback.print_exc()

