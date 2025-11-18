"""
Test Case Generator
Generates comprehensive test cases covering valid, invalid, and edge cases.
"""

import json
import random
import string
from typing import Dict, Any, List
from datetime import datetime, timedelta


class TestGenerator:
    """Generate test cases from parsed endpoints and schemas."""
    
    def __init__(self, parsed_data: Dict[str, Any]):
        self.parsed_data = parsed_data
        self.schemas = parsed_data.get('schemas', {})
        self.endpoints = parsed_data.get('endpoints', {})
    
    def _generate_valid_value(self, prop_schema: Dict[str, Any], prop_name: str) -> Any:
        """Generate a valid value for a property based on its schema."""
        prop_type = prop_schema.get('type', 'string')
        prop_format = prop_schema.get('format', '')
        
        if prop_type == 'string':
            if prop_format == 'date':
                return (datetime.now() + timedelta(days=random.randint(-30, 30))).strftime('%Y-%m-%d')
            if prop_format == 'date-time':
                return (datetime.now() + timedelta(days=random.randint(-30, 30))).isoformat()
            if prop_format == 'uuid':
                return '123e4567-e89b-12d3-a456-426614174000'
            if 'id' in prop_name.lower() or 'gid' in prop_name.lower():
                return f"test_{prop_name}_{random.randint(1000, 9999)}"
            if 'email' in prop_name.lower():
                return f"test{random.randint(100, 999)}@example.com"
            if 'url' in prop_name.lower() or prop_format == 'uri':
                return f"https://example.com/{random.randint(100, 999)}"
            return f"test_{prop_name}_{random.randint(100, 999)}"
        
        if prop_type == 'integer':
            return random.randint(1, 1000)
        
        if prop_type == 'number':
            return round(random.uniform(1.0, 100.0), 2)
        
        if prop_type == 'boolean':
            return random.choice([True, False])
        
        if prop_type == 'array':
            items = prop_schema.get('items', {})
            return [self._generate_valid_value(items, 'item') for _ in range(random.randint(1, 3))]
        
        if prop_type == 'object':
            props = prop_schema.get('properties', {})
            return {k: self._generate_valid_value(v, k) for k, v in props.items()}
        
        return None
    
    def _generate_invalid_value(self, prop_schema: Dict[str, Any], prop_name: str) -> Any:
        """Generate an invalid value for a property."""
        prop_type = prop_schema.get('type', 'string')
        
        # Generate wrong type
        if prop_type == 'string':
            return random.randint(1, 100)  # Return number instead
        if prop_type == 'integer':
            return "not_a_number"
        if prop_type == 'number':
            return "not_a_float"
        if prop_type == 'boolean':
            return "not_a_boolean"
        if prop_type == 'array':
            return "not_an_array"
        if prop_type == 'object':
            return "not_an_object"
        
        return None
    
    def _generate_edge_case_value(self, prop_schema: Dict[str, Any], prop_name: str) -> Any:
        """Generate edge case values."""
        prop_type = prop_schema.get('type', 'string')
        
        if prop_type == 'string':
            # Empty string
            if random.random() < 0.5:
                return ""
            # Very long string
            return "x" * 10000
        if prop_type == 'integer':
            # Zero, negative, very large
            return random.choice([0, -1, 999999999])
        if prop_type == 'number':
            return random.choice([0.0, -1.0, 999999.99])
        if prop_type == 'array':
            return []  # Empty array
        
        return None
    
    def generate_test_cases(self) -> List[Dict[str, Any]]:
        """Generate comprehensive test cases for all endpoints."""
        test_cases = []
        
        for endpoint_key, schema_info in self.schemas.items():
            method, path = endpoint_key.split(' ', 1)
            
            # Valid test case
            test_cases.append({
                'name': f'{endpoint_key}_valid',
                'endpoint': endpoint_key,
                'method': method,
                'path': path,
                'type': 'valid',
                'request': self._generate_valid_request(schema_info),
                'expected_status': 200
            })
            
            # Invalid test cases
            invalid_cases = self._generate_invalid_cases(endpoint_key, schema_info)
            test_cases.extend(invalid_cases)
            
            # Edge case test cases
            edge_cases = self._generate_edge_cases(endpoint_key, schema_info)
            test_cases.extend(edge_cases)
        
        return test_cases
    
    def _generate_valid_request(self, schema_info: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a valid request body."""
        request_schema = schema_info.get('request', {})
        if not request_schema or request_schema.get('type') != 'object':
            return {}
        
        request = {}
        properties = request_schema.get('properties', {})
        required = set(request_schema.get('required', []))
        
        for prop_name, prop_schema in properties.items():
            if prop_name in required:
                request[prop_name] = self._generate_valid_value(prop_schema, prop_name)
        
        return request
    
    def _generate_invalid_cases(self, endpoint_key: str, schema_info: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate invalid test cases."""
        cases = []
        method, path = endpoint_key.split(' ', 1)
        request_schema = schema_info.get('request', {})
        
        if request_schema and request_schema.get('type') == 'object':
            properties = request_schema.get('properties', {})
            required = set(request_schema.get('required', []))
            
            # Missing required field
            for req_field in list(required)[:2]:  # Test first 2 required fields
                request = self._generate_valid_request(schema_info)
                del request[req_field]
                cases.append({
                    'name': f'{endpoint_key}_missing_required_{req_field}',
                    'endpoint': endpoint_key,
                    'method': method,
                    'path': path,
                    'type': 'invalid',
                    'request': request,
                    'expected_status': 400,
                    'error_type': 'missing_required_field'
                })
            
            # Invalid type for field
            for prop_name, prop_schema in list(properties.items())[:2]:  # Test first 2 fields
                request = self._generate_valid_request(schema_info)
                request[prop_name] = self._generate_invalid_value(prop_schema, prop_name)
                cases.append({
                    'name': f'{endpoint_key}_invalid_type_{prop_name}',
                    'endpoint': endpoint_key,
                    'method': method,
                    'path': path,
                    'type': 'invalid',
                    'request': request,
                    'expected_status': 422,
                    'error_type': 'invalid_type'
                })
        
        return cases
    
    def _generate_edge_cases(self, endpoint_key: str, schema_info: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate edge case test cases."""
        cases = []
        method, path = endpoint_key.split(' ', 1)
        request_schema = schema_info.get('request', {})
        
        if request_schema and request_schema.get('type') == 'object':
            properties = request_schema.get('properties', {})
            
            # Empty strings, null values, etc.
            for prop_name, prop_schema in list(properties.items())[:2]:
                request = self._generate_valid_request(schema_info)
                request[prop_name] = self._generate_edge_case_value(prop_schema, prop_name)
                cases.append({
                    'name': f'{endpoint_key}_edge_case_{prop_name}',
                    'endpoint': endpoint_key,
                    'method': method,
                    'path': path,
                    'type': 'edge_case',
                    'request': request,
                    'expected_status': [200, 400, 422],  # Could be valid or invalid
                    'error_type': 'edge_case'
                })
        
        return cases
    
    def generate_pytest_code(self) -> str:
        """Generate pytest test code."""
        test_cases = self.generate_test_cases()
        
        code = """import pytest
import httpx
from fastapi.testclient import TestClient
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from fastapi_app.main import app
except ImportError:
    # Fallback for different project structures
    try:
        from main import app
    except ImportError:
        raise ImportError("Could not import FastAPI app. Make sure fastapi_app/main.py exists.")

client = TestClient(app)

"""
        
        for test_case in test_cases:
            test_name = test_case['name']
            # Sanitize test name to create valid Python function name
            # Replace invalid characters with underscores
            test_name = test_name.replace(' ', '_').replace('/', '_').replace('-', '_')
            test_name = test_name.replace('{', '').replace('}', '').replace('(', '').replace(')', '')
            test_name = test_name.replace('.', '_').replace(':', '_').replace('&', '_')
            test_name = test_name.replace('?', '_').replace('=', '_').replace(',', '_')
            # Remove multiple consecutive underscores
            while '__' in test_name:
                test_name = test_name.replace('__', '_')
            # Remove leading/trailing underscores
            test_name = test_name.strip('_')
            # Ensure it starts with a letter or underscore
            if test_name and not test_name[0].isalpha() and test_name[0] != '_':
                test_name = '_' + test_name
            
            method = test_case['method'].lower()
            path = test_case['path']
            request_body = test_case.get('request', {})
            expected_status = test_case.get('expected_status', 200)
            
            code += f"def test_{test_name}():\n"
            code += f'    """Test {test_case["type"]} case for {test_case["endpoint"]}"""\n'
            
            # Replace path parameters with test values
            path_with_params = path
            for param in test_case.get('path_params', []):
                path_with_params = path_with_params.replace(f'{{{param}}}', f'test_{param}')
            
            if method in ['get', 'delete']:
                code += f"    response = client.{method}('{path_with_params}')\n"
            else:
                code += f"    response = client.{method}('{path_with_params}', json={request_body})\n"
            
            if isinstance(expected_status, list):
                code += f"    assert response.status_code in {expected_status}\n"
            else:
                code += f"    assert response.status_code == {expected_status}\n"
            
            code += "\n"
        
        return code
    
    def save(self, output_path: str = 'tests/test_api.py'):
        """Save test cases to file."""
        import os
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Save as JSON
        test_cases = self.generate_test_cases()
        json_path = output_path.replace('.py', '.json')
        with open(json_path, 'w') as f:
            json.dump(test_cases, f, indent=2)
        
        # Only save pytest code if the file doesn't exist or is explicitly requested
        # This prevents overwriting the functional test file
        if os.path.exists(output_path):
            # Check if it's the functional test file (has proper imports and fixtures)
            try:
                with open(output_path, 'r') as f:
                    content = f.read()
                    # Check for markers that indicate this is the functional test file
                    if any(marker in content for marker in [
                        'from conftest import',
                        'sample_user_data',
                        'sample_workspace_data',
                        'test_create_workspace',
                        'test_create_user',
                        'test_create_project'
                    ]):
                        print(f"⚠️  Skipping test generation - functional test file exists at {output_path}")
                        print(f"   Generated test structure saved to {json_path}")
                        return
            except Exception as e:
                # If we can't read the file, proceed with caution
                print(f"⚠️  Warning: Could not check existing test file: {e}")
                # Still proceed to overwrite, but this is a fallback
        
        # Save as pytest code
        pytest_code = self.generate_pytest_code()
        with open(output_path, 'w') as f:
            f.write(pytest_code)
        
        print(f"Test cases saved to {output_path}")


if __name__ == '__main__':
    # Load parsed data
    with open('parsed_endpoints.json', 'r') as f:
        parsed_data = json.load(f)
    
    generator = TestGenerator(parsed_data)
    generator.save('tests/test_api.py')

