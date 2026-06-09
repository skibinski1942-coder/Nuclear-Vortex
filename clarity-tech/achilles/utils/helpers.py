"""
Helper Utilities
================

Common utility functions used throughout Achilles.
"""

import json
import hashlib
from typing import Any, Optional
from datetime import datetime


def generate_id(prefix: str = "id") -> str:
    """
    Generate a unique identifier.
    
    Args:
        prefix: Prefix for the ID.
        
    Returns:
        A unique string ID.
    """
    timestamp_str = datetime.now().strftime('%Y%m%d_%H%M%S_%f')
    return f"{prefix}_{timestamp_str}"


def timestamp() -> str:
    """
    Get current timestamp as ISO format string.
    
    Returns:
        ISO formatted timestamp.
    """
    return datetime.now().isoformat()


def safe_json_loads(data: str, default: Any = None) -> Any:
    """
    Safely parse JSON string.
    
    Args:
        data: JSON string to parse.
        default: Default value if parsing fails.
        
    Returns:
        Parsed JSON or default value.
    """
    try:
        return json.loads(data)
    except (json.JSONDecodeError, TypeError):
        return default


def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """
    Truncate text to specified length.
    
    Args:
        text: Text to truncate.
        max_length: Maximum length.
        suffix: Suffix to add if truncated.
        
    Returns:
        Truncated text.
    """
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix


def hash_content(content: Any) -> str:
    """
    Generate a hash of content.
    
    Args:
        content: Content to hash.
        
    Returns:
        SHA256 hash string.
    """
    content_str = json.dumps(content, sort_keys=True, default=str)
    return hashlib.sha256(content_str.encode()).hexdigest()


def merge_dicts(base: dict, override: dict) -> dict:
    """
    Deep merge two dictionaries.
    
    Args:
        base: Base dictionary.
        override: Dictionary to merge on top.
        
    Returns:
        Merged dictionary.
    """
    result = base.copy()
    
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = merge_dicts(result[key], value)
        else:
            result[key] = value
    
    return result


def format_duration(seconds: float) -> str:
    """
    Format duration in human-readable format.
    
    Args:
        seconds: Duration in seconds.
        
    Returns:
        Formatted duration string.
    """
    if seconds < 1:
        return f"{seconds * 1000:.0f}ms"
    elif seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        minutes = seconds / 60
        return f"{minutes:.1f}m"
    else:
        hours = seconds / 3600
        return f"{hours:.1f}h"


def sanitize_filename(filename: str) -> str:
    """
    Sanitize a filename by removing invalid characters.
    
    Args:
        filename: Original filename.
        
    Returns:
        Sanitized filename.
    """
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        filename = filename.replace(char, '_')
    return filename
