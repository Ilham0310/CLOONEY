"""
FastAPI Code Generator
Generates FastAPI endpoint stubs with Pydantic models from parsed schemas.
"""

import json
from typing import Dict, Any, List
from string import Template


class FastAPIGenerator:
    """Generate FastAPI application code from parsed endpoints and schemas."""
    
    def __init__(self, parsed_data: Dict[str, Any]):
        self.parsed_data = parsed_data
        # Handle both old format (with schemas) and new format (endpoints with inline schemas)
        if 'schemas' in parsed_data:
            self.schemas = parsed_data.get('schemas', {})
        else:
            # Extract schemas from endpoints
            self.schemas = {}
            for endpoint_key, endpoint_info in parsed_data.get('endpoints', {}).items():
                self.schemas[endpoint_key] = endpoint_info
        self.endpoints = parsed_data.get('endpoints', {})
    
    def _json_type_to_python(self, prop_schema: Dict[str, Any], prop_name: str) -> str:
        """Convert JSON schema type to Python/Pydantic type."""
        prop_type = prop_schema.get('type', 'string')
        prop_format = prop_schema.get('format', '')
        
        # Handle dates
        if prop_format == 'date':
            return 'date'
        if prop_format == 'date-time':
            return 'datetime'
        
        # Handle UUIDs
        if prop_format == 'uuid':
            return 'UUID'
        
        # Handle numbers
        if prop_type == 'integer':
            return 'int'
        if prop_type == 'number':
            return 'float'
        
        # Handle booleans
        if prop_type == 'boolean':
            return 'bool'
        
        # Handle arrays
        if prop_type == 'array':
            items = prop_schema.get('items', {})
            item_type = self._json_type_to_python(items, 'item')
            return f'List[{item_type}]'
        
        # Handle objects
        if prop_type == 'object':
            return 'Dict[str, Any]'
        
        # Default to string
        return 'str'
    
    def _generate_pydantic_model(self, schema: Dict[str, Any], model_name: str) -> str:
        """Generate Pydantic model from schema."""
        if not schema or schema.get('type') != 'object':
            return ''
        
        # Clean model name to be valid Python identifier
        model_name = ''.join(c if c.isalnum() or c == '_' else '_' for c in model_name)
        if model_name and not (model_name[0].isalpha() or model_name[0] == '_'):
            model_name = '_' + model_name
        
        imports = set(['from pydantic import BaseModel'])
        fields = []
        properties = schema.get('properties', {})
        required = set(schema.get('required', []))
        
        for prop_name, prop_schema in properties.items():
            # Clean property name
            clean_prop_name = prop_name
            if not (prop_name[0].isalpha() or prop_name[0] == '_'):
                clean_prop_name = '_' + prop_name
            
            python_type = self._json_type_to_python(prop_schema, prop_name)
            
            # Add imports for special types
            if 'datetime' in python_type:
                imports.add('from datetime import datetime')
            if 'date' in python_type and 'datetime' not in python_type:
                imports.add('from datetime import date')
            if 'UUID' in python_type:
                imports.add('from uuid import UUID')
            if 'List' in python_type:
                imports.add('from typing import List')
            if 'Dict' in python_type:
                imports.add('from typing import Dict, Any')
            
            # Make optional if not required
            if prop_name not in required:
                python_type = f'Optional[{python_type}]'
                imports.add('from typing import Optional')
            
            # Use field alias if property name is not valid Python identifier
            if clean_prop_name != prop_name:
                fields.append(f'    {clean_prop_name}: {python_type}  # Field name: {prop_name}')
            else:
                fields.append(f'    {prop_name}: {python_type}')
        
        model_code = '\n'.join(sorted(imports)) + '\n\n\n'
        model_code += f'class {model_name}(BaseModel):\n'
        if fields:
            model_code += '\n'.join(fields)
        else:
            model_code += '    pass'
        
        return model_code
    
    def _generate_endpoint(self, endpoint_key: str, schema_info: Dict[str, Any]) -> str:
        """Generate FastAPI endpoint function."""
        method, path = endpoint_key.split(' ', 1)
        method = method.lower()
        
        # Convert path parameters
        path_params = schema_info.get('path_params', [])
        path_with_params = path
        for param in path_params:
            path_with_params = path_with_params.replace(f'{{{param}}}', f'{{{param}: str}}')
        
        # Generate function name (must be valid Python identifier)
        func_name = f"{method}_{path.replace('/', '_').replace('{', '').replace('}', '').replace('-', '_').strip('_')}"
        # Remove any invalid characters and ensure it starts with letter/underscore
        func_name = ''.join(c if c.isalnum() or c == '_' else '_' for c in func_name)
        if func_name and not (func_name[0].isalpha() or func_name[0] == '_'):
            func_name = '_' + func_name
        # Convert to snake_case
        func_name = func_name.lower().replace('__', '_').strip('_')
        if not func_name:
            func_name = f"{method}_endpoint"
        
        # Generate endpoint code
        endpoint_code = f"@app.{method}('{path}')\n"
        endpoint_code += f"async def {func_name}("
        
        # Add path parameters (required)
        params = [f"{param}: str" for param in path_params]
        
        # Add request body (required, must come before optional params)
        request_schema = schema_info.get('request', {})
        if request_schema and method in ['post', 'put', 'patch']:
            # Generate model name matching the one in models.py (PascalCase)
            model_name = ''.join(word.capitalize() for word in func_name.split('_')) + 'Request'
            params.append(f"body: {model_name}")
        
        # Add query parameters (optional, must come after required params)
        query_params = schema_info.get('query_params', [])
        params.extend([f"{param}: Optional[str] = None" for param in query_params])
        
        endpoint_code += ', '.join(params) + "):\n"
        endpoint_code += '    """\n'
        endpoint_code += f'    {method.upper()} {path}\n'
        endpoint_code += '    """\n'
        endpoint_code += '    # TODO: Implement endpoint logic\n'
        endpoint_code += '    return {"status": "not_implemented"}\n\n'
        
        return endpoint_code
    
    def generate_models(self) -> str:
        """Generate all Pydantic models."""
        models_code = """from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime, date
from uuid import UUID

"""
        
        model_names = set()
        
        for endpoint_key, schema_info in self.schemas.items():
            # Generate request model
            request_schema = schema_info.get('request', {})
            if request_schema:
                method, path = endpoint_key.split(' ', 1)
                func_name = f"{method}_{path.replace('/', '_').replace('{', '').replace('}', '').replace('-', '_').strip('_')}"
                # Clean function name
                func_name = ''.join(c if c.isalnum() or c == '_' else '_' for c in func_name).lower()
                model_name = ''.join(word.capitalize() for word in func_name.split('_')) + 'Request'
                if model_name not in model_names:
                    models_code += self._generate_pydantic_model(request_schema, model_name) + '\n\n'
                    model_names.add(model_name)
            
            # Generate response models
            for status, response_schema in schema_info.get('responses', {}).items():
                if response_schema.get('type') == 'object':
                    method, path = endpoint_key.split(' ', 1)
                    func_name = f"{method}_{path.replace('/', '_').replace('{', '').replace('}', '').replace('-', '_').strip('_')}"
                    # Clean function name
                    func_name = ''.join(c if c.isalnum() or c == '_' else '_' for c in func_name).lower()
                    model_name = ''.join(word.capitalize() for word in func_name.split('_')) + f'Response{status}'
                    if model_name not in model_names:
                        models_code += self._generate_pydantic_model(response_schema, model_name) + '\n\n'
                        model_names.add(model_name)
        
        return models_code
    
    def generate_endpoints(self) -> str:
        """Generate all FastAPI endpoints."""
        endpoints_code = """from fastapi import FastAPI, HTTPException
from typing import Optional

app = FastAPI(title="Asana API Clone", version="1.0.0")

"""
        
        # Import models from the same directory
        endpoints_code += "try:\n"
        endpoints_code += "    from .models import *\n"
        endpoints_code += "except ImportError:\n"
        endpoints_code += "    from models import *\n\n"
        
        for endpoint_key, schema_info in self.schemas.items():
            endpoints_code += self._generate_endpoint(endpoint_key, schema_info)
        
        return endpoints_code
    
    def generate(self) -> Dict[str, str]:
        """Generate complete FastAPI application code."""
        return {
            'models': self.generate_models(),
            'endpoints': self.generate_endpoints()
        }
    
    def save(self, output_dir: str = 'fastapi_app'):
        """Save FastAPI code to files."""
        import os
        import re
        os.makedirs(output_dir, exist_ok=True)
        
        code = self.generate()
        
        # Save models
        with open(f'{output_dir}/models.py', 'w') as f:
            f.write(code['models'])
        
        # Check if main.py exists and has functional endpoints
        main_path = f'{output_dir}/main.py'
        functional_endpoints = ""
        if os.path.exists(main_path):
            with open(main_path, 'r') as f:
                existing_content = f.read()
                # Check if it has functional CRUD endpoints (database imports, SQLAlchemy usage)
                if 'from .database import' in existing_content or 'from database import' in existing_content:
                    # Extract functional endpoints (those with database operations)
                    # Look for endpoints that import database or use db_session
                    lines = existing_content.split('\n')
                    in_functional_endpoint = False
                    functional_lines = []
                    
                    # Find imports and database setup
                    for i, line in enumerate(lines):
                        if 'from .database import' in line or 'from database import' in line:
                            # Extract all imports and database-related code
                            j = i
                            while j < len(lines) and (lines[j].strip().startswith('from') or 
                                                      lines[j].strip().startswith('import') or
                                                      lines[j].strip().startswith('@app') or
                                                      'get_db' in lines[j] or
                                                      'SessionLocal' in lines[j] or
                                                      lines[j].strip() == ''):
                                functional_lines.append(lines[j])
                                j += 1
                            break
                    
                    # Extract functional endpoint definitions
                    # Look for routes that use database (have db: Session parameter or use database models)
                    endpoint_pattern = r'@app\.(get|post|put|delete)\s*\([^)]*\)\s*\n\s*(async\s+)?def\s+\w+.*?db.*?:'
                    matches = list(re.finditer(endpoint_pattern, existing_content, re.MULTILINE | re.DOTALL))
                    
                    if matches or 'get_db' in existing_content:
                        # Preserve the entire functional implementation
                        print(f"⚠️  Preserving existing functional endpoints in {main_path}")
                        # Don't overwrite - keep existing file
                        return
        
        # Save main app (only if no functional endpoints exist)
        with open(main_path, 'w') as f:
            f.write(code['endpoints'])
        
        # Create requirements file
        requirements = """fastapi>=0.104.0
uvicorn[standard]>=0.24.0
pydantic>=2.0.0
python-multipart>=0.0.6
"""
        with open(f'{output_dir}/requirements.txt', 'w') as f:
            f.write(requirements)
        
        print(f"FastAPI application saved to {output_dir}/")


if __name__ == '__main__':
    # Load parsed data
    with open('parsed_endpoints.json', 'r') as f:
        parsed_data = json.load(f)
    
    generator = FastAPIGenerator(parsed_data)
    generator.save('fastapi_app')

