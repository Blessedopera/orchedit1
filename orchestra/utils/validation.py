"""
Orchestra validation utilities
"""
import json
from typing import Dict, Any, List, Optional

def validate_node_config(config: Dict[str, Any]) -> List[str]:
    """Validate node configuration and return list of errors"""
    errors = []
    
    required_fields = ['name', 'input_schema', 'output_schema', 'language']
    for field in required_fields:
        if field not in config:
            errors.append(f"Missing required field: {field}")
    
    # Validate input_schema
    if 'input_schema' in config:
        schema = config['input_schema']
        if not isinstance(schema, dict):
            errors.append("input_schema must be a dictionary")
        else:
            if 'required' in schema and not isinstance(schema['required'], list):
                errors.append("input_schema.required must be a list")
            if 'optional' in schema and not isinstance(schema['optional'], list):
                errors.append("input_schema.optional must be a list")
    
    # Validate output_schema
    if 'output_schema' in config:
        if not isinstance(config['output_schema'], list):
            errors.append("output_schema must be a list")
    
    return errors

def validate_workflow(workflow: Dict[str, Any]) -> List[str]:
    """Validate workflow configuration and return list of errors"""
    errors = []
    
    if 'steps' not in workflow:
        errors.append("Workflow must contain 'steps' array")
        return errors
    
    steps = workflow['steps']
    if not isinstance(steps, list):
        errors.append("'steps' must be an array")
        return errors
    
    for i, step in enumerate(steps):
        if not isinstance(step, dict):
            errors.append(f"Step {i} must be an object")
            continue
        
        if 'node' not in step:
            errors.append(f"Step {i} missing 'node' field")
        
        if 'inputs' in step and not isinstance(step['inputs'], dict):
            errors.append(f"Step {i} 'inputs' must be an object")
    
    return errors