import azure.functions as func
import logging
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from shared.auth import generate_token
from shared.utils import (
    error_response,
    success_response,
    method_not_allowed_response
)
from shared.validators import (
    validate_required_fields,
    validate_email,
    validate_password,
    sanitize_email,
    sanitize_string
)
from shared.services import (
    create_user as create_user_db,
    user_exists
)

logger = logging.getLogger(__name__)


def main(req: func.HttpRequest) -> func.HttpResponse:
    """
    POST /api/auth/register
    Register a new user
    """
    try:
        if req.method != 'POST':
            return method_not_allowed_response()
        
        req_body = req.get_json()
        
        if not req_body:
            return error_response("Request body is required", 400)
        
        # Validate required fields
        is_valid, error_msg = validate_required_fields(req_body, ['email', 'password', 'name'])
        if not is_valid:
            return error_response(error_msg, 400)
        
        # Sanitize inputs
        email = sanitize_email(req_body['email'])
        password = req_body['password']
        name = sanitize_string(req_body['name'])
        role = req_body.get('role', 'user')  # Default to 'user', admin can be set manually
        
        # Validate email format
        is_valid, error_msg = validate_email(email)
        if not is_valid:
            return error_response(error_msg, 400)
        
        # Validate password strength
        is_valid, error_msg = validate_password(password)
        if not is_valid:
            return error_response(error_msg, 400)
        
        # Check if user already exists
        if user_exists(email):
            return error_response("User with this email already exists", 409)
        
        try:
            # Create user using utility function
            user = create_user_db(email, password, name, role)
            
            # Generate token
            token = generate_token(user['_id'], user['email'], user.get('role', 'user'))
            
            # Return user info with token
            user_response = {
                "_id": user['_id'],
                "email": user['email'],
                "name": user['name'],
                "role": user['role'],
                "token": token
            }
            
            return success_response(user_response, 201)
        except ValueError as e:
            return error_response(str(e), 409)
        except Exception as e:
            logger.error(f"Error creating user: {str(e)}")
            return error_response("Failed to register user", 500, str(e))
            
    except Exception as e:
        logger.error(f"Error registering user: {str(e)}")
        return error_response("Failed to register user", 500, str(e))
