"""
Validators
==========

Validation utilities for Achilles configuration and inputs.
"""

from typing import Any, Dict, List, Optional, Tuple


def validate_config(config: Dict[str, Any], schema: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Validate a configuration dictionary against a schema.
    
    Args:
        config: Configuration to validate.
        schema: Schema definition with required fields and types.
        
    Returns:
        Tuple of (is_valid, list of error messages).
    """
    errors = []
    
    # Check required fields
    required = schema.get("required", [])
    for field in required:
        if field not in config:
            errors.append(f"Missing required field: {field}")
    
    # Check field types
    field_types = schema.get("types", {})
    for field, expected_type in field_types.items():
        if field in config:
            value = config[field]
            if expected_type == "string" and not isinstance(value, str):
                errors.append(f"Field '{field}' should be a string")
            elif expected_type == "number" and not isinstance(value, (int, float)):
                errors.append(f"Field '{field}' should be a number")
            elif expected_type == "boolean" and not isinstance(value, bool):
                errors.append(f"Field '{field}' should be a boolean")
            elif expected_type == "list" and not isinstance(value, list):
                errors.append(f"Field '{field}' should be a list")
            elif expected_type == "dict" and not isinstance(value, dict):
                errors.append(f"Field '{field}' should be a dictionary")
    
    # Check field constraints
    constraints = schema.get("constraints", {})
    for field, field_constraints in constraints.items():
        if field in config:
            value = config[field]
            
            if "min" in field_constraints:
                if isinstance(value, (int, float)) and value < field_constraints["min"]:
                    errors.append(f"Field '{field}' must be >= {field_constraints['min']}")
            
            if "max" in field_constraints:
                if isinstance(value, (int, float)) and value > field_constraints["max"]:
                    errors.append(f"Field '{field}' must be <= {field_constraints['max']}")
            
            if "min_length" in field_constraints:
                if hasattr(value, '__len__') and len(value) < field_constraints["min_length"]:
                    errors.append(f"Field '{field}' must have at least {field_constraints['min_length']} items")
            
            if "max_length" in field_constraints:
                if hasattr(value, '__len__') and len(value) > field_constraints["max_length"]:
                    errors.append(f"Field '{field}' must have at most {field_constraints['max_length']} items")
            
            if "choices" in field_constraints:
                if value not in field_constraints["choices"]:
                    errors.append(f"Field '{field}' must be one of: {field_constraints['choices']}")
    
    return len(errors) == 0, errors


def validate_task_params(
    params: Dict[str, Any],
    required: Optional[List[str]] = None,
    optional: Optional[List[str]] = None
) -> Tuple[bool, List[str]]:
    """
    Validate task parameters.
    
    Args:
        params: Parameters to validate.
        required: List of required parameter names.
        optional: List of optional parameter names.
        
    Returns:
        Tuple of (is_valid, list of error messages).
    """
    errors = []
    required = required or []
    optional = optional or []
    
    # Check required parameters
    for param in required:
        if param not in params or params[param] is None:
            errors.append(f"Missing required parameter: {param}")
    
    # Check for unknown parameters
    known = set(required) | set(optional)
    for param in params:
        if param not in known:
            # Just a warning, not an error
            pass
    
    return len(errors) == 0, errors


def validate_json_structure(
    data: Any,
    expected_type: str = "any"
) -> Tuple[bool, str]:
    """
    Validate JSON data structure.
    
    Args:
        data: Data to validate.
        expected_type: Expected type (any, object, array, string, number, boolean).
        
    Returns:
        Tuple of (is_valid, error message or empty string).
    """
    if expected_type == "any":
        return True, ""
    
    type_mapping = {
        "object": dict,
        "array": list,
        "string": str,
        "number": (int, float),
        "boolean": bool,
    }
    
    expected = type_mapping.get(expected_type)
    if expected is None:
        return False, f"Unknown expected type: {expected_type}"
    
    if not isinstance(data, expected):
        actual_type = type(data).__name__
        return False, f"Expected {expected_type}, got {actual_type}"
    
    return True, ""


def validate_priority(priority: str) -> Tuple[bool, str]:
    """
    Validate a priority value.
    
    Args:
        priority: Priority string to validate.
        
    Returns:
        Tuple of (is_valid, error message or empty string).
    """
    valid_priorities = ["CRITICAL", "HIGH", "MEDIUM", "LOW", "BACKGROUND"]
    
    if priority.upper() not in valid_priorities:
        return False, f"Invalid priority. Must be one of: {valid_priorities}"
    
    return True, ""


def sanitize_input(text: str, max_length: int = 10000) -> str:
    """
    Sanitize user input.
    
    Args:
        text: Input text.
        max_length: Maximum allowed length.
        
    Returns:
        Sanitized text.
    """
    # Truncate if too long
    if len(text) > max_length:
        text = text[:max_length]
    
    # Remove null bytes
    text = text.replace('\x00', '')
    
    # Normalize whitespace
    text = ' '.join(text.split())
    
    return text
