#!/usr/bin/env python3
"""
Integrate WebSocket CRUD data into the existing network parser pipeline.
This converts WebSocket operations to the format expected by the network parser.
"""

import json
from typing import Dict, Any, List

def convert_websocket_to_network_format(websocket_file: str, rest_endpoints_file: str) -> Dict[str, Any]:
    """Convert WebSocket data to network parser format."""
    
    with open(rest_endpoints_file, 'r') as f:
        rest_data = json.load(f)
    
    endpoints = rest_data.get('endpoints', {})
    
    # Convert to network parser format
    parsed_endpoints = {}
    
    for endpoint_key, endpoint_info in endpoints.items():
        # Include all CRUD entities
        entity_type = endpoint_info.get('entity_type', '')
        # Include Task, ColumnTask (also tasks), Pot (Project), Column (Section), User, Team, and Domain (Workspace)
        if entity_type not in ['Task', 'ColumnTask', 'Pot', 'Column', 'User', 'Team', 'Domain']:
            continue
        
        method = endpoint_info['method']
        path = endpoint_info['path']
        
        # Normalize path (replace {id} with placeholder)
        normalized_path = path.replace('{id}', '{id}')
        
        endpoint_id = f"{method} {normalized_path}"
        
        if endpoint_id not in parsed_endpoints:
            parsed_endpoints[endpoint_id] = {
                'methods': {method},
                'requests': [],
                'responses': {},
                'query_params': set(),
                'path_params': ['id'] if '{id}' in path else []
            }
        
        # Add request schema
        request_schema = endpoint_info.get('request_schema', {})
        if request_schema:
            parsed_endpoints[endpoint_id]['requests'].append({
                'body': request_schema,
                'headers': {'content-type': 'application/json'}
            })
        
        # Add response schema
        response_schema = endpoint_info.get('response_schema', {})
        if response_schema:
            status = '200'
            parsed_endpoints[endpoint_id]['responses'][status] = response_schema
    
    # Convert sets to lists
    result = {}
    for key, info in parsed_endpoints.items():
        result[key] = {
            'methods': list(info['methods']),
            'requests': info['requests'],
            'responses': info['responses'],
            'query_params': list(info['query_params']),
            'path_params': list(info['path_params'])
        }
    
    return {
        'endpoints': result,
        'relationships': {},  # Can be inferred later
        'metadata': {
            'source': 'websocket_capture',
            'total_endpoints': len(result)
        }
    }

if __name__ == '__main__':
    import sys
    
    rest_file = 'rest_endpoints_from_websocket.json'
    output_file = 'parsed_endpoints_from_websocket.json'
    
    try:
        result = convert_websocket_to_network_format(None, rest_file)
        
        with open(output_file, 'w') as f:
            json.dump(result, f, indent=2, default=str)
        
        print("=" * 80)
        print("WEBSOCKET DATA INTEGRATION")
        print("=" * 80)
        print(f"\n✅ Converted {result['metadata']['total_endpoints']} endpoints")
        print(f"✅ Saved to {output_file}")
        print(f"\nYou can now use this file with the existing pipeline:")
        print(f"  python run_pipeline.py --mode generate")
        print(f"\nOr copy it to parsed_endpoints.json:")
        print(f"  cp {output_file} parsed_endpoints.json")
        
    except FileNotFoundError as e:
        print(f"Error: {e}")
        print("Run websocket_to_rest_converter.py first to generate REST endpoints.")
    except Exception as e:
        import traceback
        print(f"Error: {e}")
        traceback.print_exc()

