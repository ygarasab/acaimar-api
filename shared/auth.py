"""
JWT authentication utilities for Azure Functions
"""
import os
import jwt
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict
from functools import wraps
import azure.functions as func
from shared.utils.responses import unauthorized_response, forbidden_response

logger = logging.getLogger(__name__)

# JWT Configuration
JWT_SECRET = os.environ.get('JWT_SECRET', 'your-secret-key-change-in-production')
JWT_ALGORITHM = 'HS256'
JWT_EXPIRATION_HOURS = 24


def generate_token(user_id: str, email: str, role: str = 'user') -> str:
    """
    Generate a JWT token for a user
    
    Args:
        user_id: User's MongoDB ObjectId as string
        email: User's email
        role: User's role (default: 'user')
    
    Returns:
        JWT token string
    """
    payload = {
        'user_id': user_id,
        'email': email,
        'role': role,
        'exp': datetime.utcnow() + timedelta(hours=JWT_EXPIRATION_HOURS),
        'iat': datetime.utcnow()
    }
    
    token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
    return token


def verify_token(token: str) -> Optional[Dict]:
    """
    Verify and decode a JWT token
    
    Args:
        token: JWT token string
    
    Returns:
        Decoded token payload if valid, None otherwise
    """
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        logger.warning("Token has expired")
        return None
    except jwt.InvalidTokenError as e:
        logger.warning(f"Invalid token: {str(e)}")
        return None


def get_token_from_request(req: func.HttpRequest) -> Optional[str]:
    """
    Extract JWT token from request headers
    
    Args:
        req: Azure Functions HTTP request
    
    Returns:
        Token string if found, None otherwise
    """
    auth_header = req.headers.get('Authorization', '')
    
    if not auth_header:
        return None
    
    # Support both "Bearer <token>" and just "<token>" formats
    if auth_header.startswith('Bearer '):
        return auth_header[7:]
    return auth_header


def require_auth(require_role: Optional[str] = None):
    """
    Decorator to require authentication for Azure Functions
    
    Args:
        require_role: Optional role requirement (e.g., 'admin')
    
    Usage:
        @require_auth()
        def my_function(req: func.HttpRequest) -> func.HttpResponse:
            ...
    """
    def decorator(func_handler):
        @wraps(func_handler)
        def wrapper(req: func.HttpRequest) -> func.HttpResponse:
            try:
                token = get_token_from_request(req)
                
                if not token:
                    return unauthorized_response("Authentication required. Please provide a valid token.")
                
                payload = verify_token(token)
                
                if not payload:
                    return unauthorized_response("Invalid or expired token. Please login again.")
                
                # Check role if required
                if require_role and payload.get('role') != require_role:
                    return forbidden_response(f"This endpoint requires '{require_role}' role. Your current role is '{payload.get('role', 'user')}'.")
                
                # Attach user info to request for use in handler
                req.user = payload
                
                return func_handler(req)
            except Exception as e:
                logger.error(f"Error in authentication decorator: {str(e)}")
                return unauthorized_response(f"Authentication error: {str(e)}")
        
        return wrapper
    return decorator
