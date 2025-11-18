#!/usr/bin/env python3
"""
Extract entity types (Task, Project, etc.) from WebSocket DbObject operations.
This will help us understand what CRUD operations are available.
"""

import json
from collections import defaultdict
from typing import Dict, Any, List

def extract_entities(capture_file: str) -> Dict[str, Any]:
    """Extract entity types and their schemas from WebSocket messages."""
    with open(capture_file, 'r') as f:
        data = json.load(f)
    
    # Check if we have structured websocket_message data
    ws_messages = data.get('websocket_messages', [])
    js_api_calls = data.get('js_api_calls', [])
    
    # Extract DbObject operations
    db_objects = []
    entity_types = defaultdict(list)
    entity_schemas = defaultdict(lambda: {'fields': set(), 'operations': set(), 'samples': []})
    
    # Process structured websocket messages first
    for ws_msg in ws_messages:
        message_data = ws_msg.get('message', [])
        if isinstance(message_data, list):
            for item in message_data:
                if item.get('collection') == 'DbObject':
                    op = item.get('msg', '')
                    fields = item.get('fields', {})
                    obj_id = item.get('id', '')
                    
                    # Get entity type from typeName field
                    entity_type = fields.get('typeName', 'Unknown')
                    
                    if entity_type and entity_type != 'Unknown':
                        entity_types[entity_type].append({
                            'operation': op,
                            'id': obj_id,
                            'fields': fields,
                            'timestamp': ws_msg.get('timestamp', '')
                        })
                        
                        # Collect schema
                        for field_name in fields.keys():
                            entity_schemas[entity_type]['fields'].add(field_name)
                        entity_schemas[entity_type]['operations'].add(op)
                        
                        # Store sample (keep first 3)
                        if len(entity_schemas[entity_type]['samples']) < 3:
                            entity_schemas[entity_type]['samples'].append({
                                'id': obj_id,
                                'operation': op,
                                'fields': {k: v for k, v in list(fields.items())[:10]}  # First 10 fields
                            })
    
    # Also try to parse from console messages if structured data not available
    if not ws_messages:
        for call in js_api_calls:
            message = call.get('message', '')
            if '[WEBSOCKET MESSAGE]' in message:
                try:
                    # Extract JSON from message
                    start_idx = message.find(' [')
                    if start_idx == -1:
                        start_idx = message.find('[')
                    
                    if start_idx != -1:
                        json_part = message[start_idx + 1:].strip()
                        
                        # Handle truncated messages - find complete JSON
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
                        
                        parsed = json.loads(json_part)
                        if isinstance(parsed, list):
                            for item in parsed:
                                if item.get('collection') == 'DbObject':
                                    op = item.get('msg', '')
                                    fields = item.get('fields', {})
                                    obj_id = item.get('id', '')
                                    
                                    # Get entity type from typeName field
                                    entity_type = fields.get('typeName', 'Unknown')
                                    
                                    if not entity_type or entity_type == 'Unknown':
                                        # Try to determine from fields
                                        if 'name' in fields and 'project' in str(fields).lower():
                                            entity_type = 'Project'
                                        elif 'name' in fields and ('task' in str(fields).lower() or 'assignee' in str(fields).lower()):
                                            entity_type = 'Task'
                                        elif 'section' in str(fields).lower() or 'column' in str(fields).lower():
                                            entity_type = 'Section'
                                        elif 'user' in str(fields).lower() or 'email' in str(fields).lower():
                                            entity_type = 'User'
                                    
                                    if entity_type and entity_type != 'Unknown':
                                        entity_types[entity_type].append({
                                            'operation': op,
                                            'id': obj_id,
                                            'fields': fields,
                                            'timestamp': call.get('timestamp', '')
                                        })
                                        
                                        # Collect schema
                                        for field_name in fields.keys():
                                            entity_schemas[entity_type]['fields'].add(field_name)
                                        entity_schemas[entity_type]['operations'].add(op)
                                    
                                    # Store all DbObjects for analysis
                                    db_objects.append({
                                        'operation': op,
                                        'id': obj_id,
                                        'fields': fields,
                                        'timestamp': call.get('timestamp', '')
                                    })
                except (json.JSONDecodeError, IndexError, KeyError):
                    pass
    
    # Convert sets to lists for JSON serialization
    schemas = {}
    for entity_type, schema in entity_schemas.items():
        schemas[entity_type] = {
            'fields': sorted(list(schema['fields'])),
            'operations': sorted(list(schema['operations'])),
            'sample_count': len(entity_types[entity_type]),
            'samples': schema['samples']
        }
    
    return {
        'total_db_objects': len(db_objects),
        'entity_types': {k: len(v) for k, v in entity_types.items()},
        'entity_schemas': schemas,
        'sample_objects': {k: v[:5] for k, v in entity_types.items()}
    }

if __name__ == '__main__':
    import sys
    capture_file = sys.argv[1] if len(sys.argv) > 1 else 'js_api_capture.json'
    
    try:
        result = extract_entities(capture_file)
        print("=" * 80)
        print("ENTITY EXTRACTION FROM WEBSOCKET MESSAGES")
        print("=" * 80)
        print(f"\nTotal DbObject operations: {result['total_db_objects']}")
        print(f"\nEntity types found:")
        for entity_type, count in result['entity_types'].items():
            print(f"  {entity_type}: {count} operations")
        
        print(f"\nEntity schemas:")
        for entity_type, schema in result['entity_schemas'].items():
            print(f"\n  {entity_type}:")
            print(f"    Operations: {', '.join(schema['operations'])}")
            print(f"    Fields ({len(schema['fields'])}): {', '.join(schema['fields'][:20])}")
            if len(schema['fields']) > 20:
                print(f"    ... and {len(schema['fields']) - 20} more")
        
        # Save detailed results
        output_file = 'websocket_entities.json'
        with open(output_file, 'w') as f:
            json.dump(result, f, indent=2, default=str)
        print(f"\n✅ Detailed results saved to {output_file}")
        
    except FileNotFoundError:
        print(f"Error: {capture_file} not found")
    except Exception as e:
        import traceback
        print(f"Error: {e}")
        traceback.print_exc()

