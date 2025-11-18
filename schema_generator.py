"""
Database Schema Generator
Generates SQL schema from parsed network data and entity relationships.
"""

import json
from typing import Dict, Any, List, Set


class SchemaGenerator:
    """Generate SQL database schema from parsed endpoints and schemas."""
    
    def __init__(self, parsed_data: Dict[str, Any]):
        self.parsed_data = parsed_data
        self.schemas = parsed_data.get('schemas', {})
        self.relationships = parsed_data.get('relationships', {})
        self.entities = self._extract_entities()
    
    def _extract_entities(self) -> Dict[str, Dict[str, Any]]:
        """Extract entity definitions from schemas."""
        entities = {}
        
        for endpoint_key, schema_info in self.schemas.items():
            # Look for entity patterns in response schemas
            for status, response_schema in schema_info.get('responses', {}).items():
                if response_schema.get('type') == 'object':
                    props = response_schema.get('properties', {})
                    
                    # Identify entity by common fields
                    entity_name = self._identify_entity(props, endpoint_key)
                    if entity_name:
                        if entity_name not in entities:
                            entities[entity_name] = {
                                'properties': {},
                                'required': set(),
                                'indexes': []
                            }
                        
                        # Merge properties
                        for prop_name, prop_schema in props.items():
                            entities[entity_name]['properties'][prop_name] = prop_schema
                            if prop_name in response_schema.get('required', []):
                                entities[entity_name]['required'].add(prop_name)
        
        return entities
    
    def _identify_entity(self, properties: Dict[str, Any], endpoint_key: str) -> str:
        """Identify entity name from properties and endpoint."""
        # Check endpoint path
        path = endpoint_key.split(' ', 1)[1] if ' ' in endpoint_key else endpoint_key
        
        if '/projects' in path or '/project' in path:
            return 'projects'
        elif '/tasks' in path or '/task' in path:
            return 'tasks'
        elif '/sections' in path or '/section' in path:
            return 'sections'
        elif '/users' in path or '/user' in path:
            return 'users'
        elif '/workspaces' in path or '/workspace' in path:
            return 'workspaces'
        elif '/teams' in path or '/team' in path:
            return 'teams'
        
        # Check properties
        prop_names = set(properties.keys())
        if 'project_id' in prop_names or 'project_gid' in prop_names:
            return 'projects'
        if 'task_id' in prop_names or 'task_gid' in prop_names:
            return 'tasks'
        if 'section_id' in prop_names or 'section_gid' in prop_names:
            return 'sections'
        if 'user_id' in prop_names or 'user_gid' in prop_names:
            return 'users'
        
        return None
    
    def _json_type_to_sql(self, prop_schema: Dict[str, Any], prop_name: str) -> str:
        """Convert JSON schema type to SQL type."""
        prop_type = prop_schema.get('type', 'string')
        prop_format = prop_schema.get('format', '')
        
        # Handle ID fields
        if 'id' in prop_name.lower() or 'gid' in prop_name.lower():
            return 'VARCHAR(255) PRIMARY KEY' if 'id' in prop_name.lower() and prop_name.lower() in ['id', 'gid'] else 'VARCHAR(255)'
        
        # Handle dates
        if prop_format == 'date' or prop_format == 'date-time':
            return 'TIMESTAMP'
        
        # Handle UUIDs
        if prop_format == 'uuid':
            return 'UUID'
        
        # Handle numbers
        if prop_type == 'integer':
            return 'INTEGER'
        if prop_type == 'number':
            return 'DECIMAL(10, 2)'
        
        # Handle booleans
        if prop_type == 'boolean':
            return 'BOOLEAN'
        
        # Handle arrays (store as JSON or create junction table)
        if prop_type == 'array':
            return 'JSONB'
        
        # Handle objects (store as JSON)
        if prop_type == 'object':
            return 'JSONB'
        
        # Default to text
        return 'TEXT'
    
    def _generate_table(self, entity_name: str, entity_data: Dict[str, Any]) -> str:
        """Generate SQL CREATE TABLE statement."""
        table_name = entity_name.lower()
        columns = []
        primary_key = None
        
        # Add standard fields
        if 'id' in entity_data['properties']:
            primary_key = 'id'
        elif 'gid' in entity_data['properties']:
            primary_key = 'gid'
        else:
            # Add auto-increment ID if none exists
            columns.append('    id SERIAL PRIMARY KEY')
        
        # Add entity-specific columns
        for prop_name, prop_schema in entity_data['properties'].items():
            if prop_name in ['id', 'gid'] and primary_key == prop_name:
                sql_type = self._json_type_to_sql(prop_schema, prop_name)
                columns.append(f'    {prop_name} {sql_type}')
            else:
                sql_type = self._json_type_to_sql(prop_schema, prop_name)
                nullable = 'NOT NULL' if prop_name in entity_data['required'] else 'NULL'
                columns.append(f'    {prop_name} {sql_type} {nullable}')
        
        # Add timestamps
        columns.append('    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP')
        columns.append('    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP')
        
        # Build CREATE TABLE statement
        sql = f"CREATE TABLE IF NOT EXISTS {table_name} (\n"
        sql += ',\n'.join(columns)
        
        if primary_key and primary_key != 'id':
            sql += f',\n    PRIMARY KEY ({primary_key})'
        
        sql += '\n);\n'
        
        # Add indexes
        if 'name' in entity_data['properties']:
            sql += f'CREATE INDEX IF NOT EXISTS idx_{table_name}_name ON {table_name}(name);\n'
        if 'created_at' in entity_data['properties'] or True:  # Always index created_at
            sql += f'CREATE INDEX IF NOT EXISTS idx_{table_name}_created_at ON {table_name}(created_at);\n'
        
        return sql
    
    def _generate_foreign_keys(self) -> str:
        """Generate foreign key constraints based on relationships."""
        fk_statements = []
        
        # Common relationships
        relationships = {
            'tasks': ['project_id', 'section_id', 'assignee_id'],
            'sections': ['project_id'],
            'projects': ['workspace_id', 'team_id'],
        }
        
        for table, fk_fields in relationships.items():
            for fk_field in fk_fields:
                # Determine referenced table
                ref_table = fk_field.replace('_id', 's').replace('_gid', 's')
                if ref_table == 'assignees':
                    ref_table = 'users'
                
                fk_statements.append(
                    f"ALTER TABLE {table} ADD CONSTRAINT fk_{table}_{fk_field} "
                    f"FOREIGN KEY ({fk_field}) REFERENCES {ref_table}(id) ON DELETE CASCADE;"
                )
        
        return '\n'.join(fk_statements) + '\n' if fk_statements else ''
    
    def generate(self) -> str:
        """Generate complete SQL schema."""
        sql = "-- Asana API Clone Database Schema\n"
        sql += "-- Generated from network traffic analysis\n\n"
        
        # Generate tables for each entity
        for entity_name, entity_data in self.entities.items():
            sql += f"-- Table: {entity_name}\n"
            sql += self._generate_table(entity_name, entity_data)
            sql += '\n'
        
        # Generate junction tables for many-to-many relationships
        sql += self._generate_junction_tables()
        
        # Generate foreign keys
        sql += "-- Foreign Key Constraints\n"
        sql += self._generate_foreign_keys()
        
        return sql
    
    def _generate_junction_tables(self) -> str:
        """Generate junction tables for many-to-many relationships."""
        sql = "-- Junction Tables for Many-to-Many Relationships\n\n"
        
        # Project members (users-projects)
        sql += """CREATE TABLE IF NOT EXISTS project_members (
    project_id VARCHAR(255) NOT NULL,
    user_id VARCHAR(255) NOT NULL,
    role VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (project_id, user_id),
    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_project_members_project_id ON project_members(project_id);
CREATE INDEX IF NOT EXISTS idx_project_members_user_id ON project_members(user_id);

"""

        # Task followers (users-tasks)
        sql += """CREATE TABLE IF NOT EXISTS task_followers (
    task_id VARCHAR(255) NOT NULL,
    user_id VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (task_id, user_id),
    FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_task_followers_task_id ON task_followers(task_id);
CREATE INDEX IF NOT EXISTS idx_task_followers_user_id ON task_followers(user_id);

"""
        
        return sql
    
    def save(self, output_path: str = 'schema.sql'):
        """Save SQL schema to file."""
        sql = self.generate()
        with open(output_path, 'w') as f:
            f.write(sql)
        print(f"SQL schema saved to {output_path}")


if __name__ == '__main__':
    # Load parsed data
    with open('parsed_endpoints.json', 'r') as f:
        parsed_data = json.load(f)
    
    generator = SchemaGenerator(parsed_data)
    generator.save('schema.sql')

