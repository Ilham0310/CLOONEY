#!/usr/bin/env python3
"""
Parser for WebSocket messages from Asana's sync API.
Extracts CRUD operations from WebSocket messages.
"""

import json
from typing import List, Dict, Any
from collections import defaultdict

def parse_websocket_messages(capture_file: str) -> Dict[str, Any]:
    """Parse WebSocket messages from capture file."""
    with open(capture_file, 'r') as f:
        data = json.load(f)
    
    # Check if we have structured data or console messages
    if 'websocket_messages' in data:
        ws_messages = data.get('websocket_messages', [])
        crud_operations = data.get('crud_operations', [])
    else:
        # Parse from console messages
        js_api_calls = data.get('js_api_calls', [])
        ws_messages = []
        crud_operations = []
        
        for call in js_api_calls:
            message = call.get('message', '')
            if '[WEBSOCKET MESSAGE]' in message:
                # Extract JSON from message string
                # Format: "[WEBSOCKET MESSAGE] url [json_data]"
                try:
                    # Find the JSON part after the URL
                    # Format: "[WEBSOCKET MESSAGE] url [json_data..."
                    # The JSON might be truncated, so we need to extract what we can
                    start_idx = message.find(' [')
                    if start_idx == -1:
                        start_idx = message.find('[')
                    
                    if start_idx != -1:
                        json_part = message[start_idx + 1:].strip()
                        # Try to parse - might be truncated, so we'll try to fix it
                        # Remove trailing incomplete parts
                        if json_part.endswith('...') or json_part.count('[') > json_part.count(']'):
                            # Truncated, try to extract what we can
                            # Find the last complete JSON object
                            bracket_count = 0
                            end_idx = 0
                            for i, char in enumerate(json_part):
                                if char == '[':
                                    bracket_count += 1
                                elif char == ']':
                                    bracket_count -= 1
                                    if bracket_count == 0:
                                        end_idx = i + 1
                                        break
                            if end_idx > 0:
                                json_part = json_part[:end_idx]
                        
                        # Try to parse the JSON
                        parsed = json.loads(json_part)
                        ws_messages.append({
                            'timestamp': call.get('timestamp', ''),
                            'message': parsed,
                            'raw': message
                        })
                        
                        # Extract CRUD operations
                        if isinstance(parsed, list):
                            for item in parsed:
                                msg_type = item.get('msg', '')
                                if msg_type in ['added', 'changed', 'removed', 'committed', 'batch_removed']:
                                    crud_operations.append({
                                        'operation': msg_type,
                                        'collection': item.get('collection', ''),
                                        'id': item.get('id', ''),
                                        'fields': item.get('fields', {}),
                                        'syncables': item.get('syncables', []),
                                        'timestamp': call.get('timestamp', '')
                                    })
                        elif isinstance(parsed, dict):
                            msg_type = parsed.get('msg', '')
                            if msg_type in ['added', 'changed', 'removed', 'committed', 'batch_removed']:
                                crud_operations.append({
                                    'operation': msg_type,
                                    'collection': parsed.get('collection', ''),
                                    'id': parsed.get('id', ''),
                                    'fields': parsed.get('fields', {}),
                                    'syncables': parsed.get('syncables', []),
                                    'timestamp': call.get('timestamp', '')
                                })
                except (json.JSONDecodeError, IndexError) as e:
                    # Skip if we can't parse
                    pass
    
    # Group operations by collection
    by_collection = defaultdict(list)
    by_operation = defaultdict(int)
    
    for op in crud_operations:
        collection = op.get('collection', 'unknown')
        operation = op.get('operation', 'unknown')
        by_collection[collection].append(op)
        by_operation[operation] += 1
    
    # Extract unique endpoints/patterns
    endpoints = set()
    for op in crud_operations:
        collection = op.get('collection', '')
        operation = op.get('operation', '')
        if collection and operation:
            endpoints.add(f"{operation.upper()} {collection}")
    
    return {
        'total_operations': len(crud_operations),
        'operations_by_type': dict(by_operation),
        'operations_by_collection': {k: len(v) for k, v in by_collection.items()},
        'endpoints': sorted(list(endpoints)),
        'sample_operations': crud_operations[:20]
    }

if __name__ == '__main__':
    import sys
    capture_file = sys.argv[1] if len(sys.argv) > 1 else 'js_api_capture.json'
    
    try:
        result = parse_websocket_messages(capture_file)
        print("=" * 80)
        print("WEBSOCKET CRUD OPERATIONS ANALYSIS")
        print("=" * 80)
        print(f"\nTotal CRUD operations: {result['total_operations']}")
        print(f"\nOperations by type:")
        for op_type, count in result['operations_by_type'].items():
            print(f"  {op_type}: {count}")
        print(f"\nOperations by collection:")
        for coll, count in result['operations_by_collection'].items():
            print(f"  {coll}: {count}")
        print(f"\nUnique endpoint patterns:")
        for endpoint in result['endpoints']:
            print(f"  {endpoint}")
    except FileNotFoundError:
        print(f"Error: {capture_file} not found")
        print("Run capture_with_js_interception.py first to generate the capture file.")
    except Exception as e:
        print(f"Error parsing file: {e}")

