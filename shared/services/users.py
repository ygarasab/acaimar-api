"""
User database operations
"""
import bcrypt
from datetime import datetime, timezone
from typing import Dict, Optional, Any, List
from shared.db_connection import get_collection
from shared.utils import convert_objectids_in_list, sanitize_user_response


def hash_password(password: str) -> str:
    """
    Hash a password using bcrypt
    
    Args:
        password: Plain text password
    
    Returns:
        Hashed password string
    """
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')


def verify_password(password: str, password_hash: str) -> bool:
    """
    Verify a password against a hash
    
    Args:
        password: Plain text password
        password_hash: Hashed password
    
    Returns:
        True if password matches, False otherwise
    """
    try:
        return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))
    except Exception:
        return False


def find_user_by_email(email: str) -> Optional[Dict[str, Any]]:
    """
    Find a user by email address
    
    Args:
        email: Email address (will be lowercased)
    
    Returns:
        User document or None if not found
    """
    collection = get_collection('users')
    return collection.find_one({"email": email.lower().strip()})


def user_exists(email: str) -> bool:
    """
    Check if a user exists by email
    
    Args:
        email: Email address
    
    Returns:
        True if user exists, False otherwise
    """
    return find_user_by_email(email) is not None


def get_all_users(exclude_password: bool = True) -> List[Dict[str, Any]]:
    """
    Get all users from database
    
    Args:
        exclude_password: Whether to exclude password hash from results
    
    Returns:
        List of user documents
    """
    collection = get_collection('users')
    projection = {"password_hash": 0} if exclude_password else {}
    users = list(collection.find({}, projection))
    
    # Convert ObjectIds to strings
    users = convert_objectids_in_list(users)
    
    return users


def create_user(email: str, password: str, name: str, role: str = 'user') -> Dict[str, Any]:
    """
    Create a new user in the database
    
    Args:
        email: User email
        password: Plain text password (will be hashed)
        name: User name
        role: User role (default: 'user')
    
    Returns:
        Created user document (without password hash)
    
    Raises:
        ValueError: If user already exists
    """
    collection = get_collection('users')
    email = email.lower().strip()
    
    # Check if user already exists
    if user_exists(email):
        raise ValueError("User with this email already exists")
    
    # Hash password
    password_hash = hash_password(password)
    
    # Create user document
    user_doc = {
        "email": email,
        "password_hash": password_hash,
        "name": name.strip(),
        "role": role,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "active": True
    }
    
    # Insert user
    result = collection.insert_one(user_doc)
    user_id = str(result.inserted_id)
    
    # Return user without password
    user_doc['_id'] = user_id
    return sanitize_user_response(user_doc)


def update_user_role(email: str, new_role: str) -> bool:
    """
    Update a user's role
    
    Args:
        email: User email
        new_role: New role to assign
    
    Returns:
        True if updated, False if user not found
    """
    collection = get_collection('users')
    result = collection.update_one(
        {"email": email.lower().strip()},
        {"$set": {"role": new_role}}
    )
    return result.modified_count > 0


def authenticate_user(email: str, password: str) -> Optional[Dict[str, Any]]:
    """
    Authenticate a user with email and password
    
    Args:
        email: User email
        password: Plain text password
    
    Returns:
        User document if authentication succeeds, None otherwise
    """
    user = find_user_by_email(email)
    
    if not user:
        return None
    
    # Check if user is active
    if not user.get('active', True):
        return None
    
    # Verify password
    password_hash = user.get('password_hash', '')
    if not password_hash or not verify_password(password, password_hash):
        return None
    
    # Return user without password
    return sanitize_user_response(user)

