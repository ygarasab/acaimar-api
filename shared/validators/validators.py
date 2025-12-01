"""
Validation utilities
"""
import re
from typing import List, Optional, Tuple


def validate_email(email: str) -> Tuple[bool, Optional[str]]:
    """
    Validate email format
    
    Args:
        email: Email address to validate
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not email or not isinstance(email, str):
        return False, "Email is required"
    
    email = email.strip().lower()
    
    # Basic email regex
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    
    if not re.match(pattern, email):
        return False, "Invalid email format"
    
    return True, None


def validate_password(password: str, min_length: int = 8) -> Tuple[bool, Optional[str]]:
    """
    Validate password strength
    
    Args:
        password: Password to validate
        min_length: Minimum password length
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not password or not isinstance(password, str):
        return False, "Password is required"
    
    if len(password) < min_length:
        return False, f"Password must be at least {min_length} characters"
    
    return True, None


def validate_required_fields(data: dict, fields: List[str]) -> Tuple[bool, Optional[str]]:
    """
    Validate that required fields are present in data
    
    Args:
        data: Dictionary to validate
        fields: List of required field names
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not isinstance(data, dict):
        return False, "Request body must be a JSON object"
    
    for field in fields:
        if field not in data or data[field] is None or data[field] == "":
            return False, f"Field '{field}' is required"
    
    return True, None


def sanitize_email(email: str) -> str:
    """
    Sanitize email address (lowercase and strip)
    
    Args:
        email: Email address
    
    Returns:
        Sanitized email
    """
    return email.lower().strip() if email else ""


def sanitize_string(value: str) -> str:
    """
    Sanitize string (strip whitespace)
    
    Args:
        value: String value
    
    Returns:
        Sanitized string
    """
    return value.strip() if value else ""

