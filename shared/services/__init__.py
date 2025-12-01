"""
Service layer for database operations
"""
from .user_service import (
    hash_password,
    verify_password,
    find_user_by_email,
    user_exists,
    get_all_users,
    create_user,
    update_user_role,
    authenticate_user
)

__all__ = [
    'hash_password',
    'verify_password',
    'find_user_by_email',
    'user_exists',
    'get_all_users',
    'create_user',
    'update_user_role',
    'authenticate_user'
]
