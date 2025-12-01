import azure.functions as func
import logging
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from shared.auth import generate_token
from shared.utils import (
    error_response,
    success_response,
    method_not_allowed_response,
    unauthorized_response
)
from shared.validators import (
    validate_required_fields,
    sanitize_email
)
from shared.services import authenticate_user

logger = logging.getLogger(__name__)


def main(req: func.HttpRequest) -> func.HttpResponse:
    """
    POST /api/auth/login
    Authenticate user and return JWT token
    """
    try:
        if req.method == 'OPTIONS':
            # Handle CORS preflight
            return func.HttpResponse(
                "",
                status_code=200,
                headers={
                    "Access-Control-Allow-Origin": "*",
                    "Access-Control-Allow-Methods": "POST, OPTIONS",
                    "Access-Control-Allow-Headers": "Content-Type, Authorization, X-Requested-With",
                    "Access-Control-Max-Age": "3600"
                }
            )
        
        if req.method != 'POST':
            return method_not_allowed_response()
        
        req_body = req.get_json()
        
        if not req_body:
            return error_response("Request body is required", 400)
        
        # Validate required fields
        is_valid, error_msg = validate_required_fields(req_body, ['email', 'password'])
        if not is_valid:
            return error_response(error_msg, 400)
        
        email = sanitize_email(req_body['email'])
        password = req_body['password']
        
        # Authenticate user
        user = authenticate_user(email, password)
        
        if not user:
            # Don't reveal if user exists or not (security best practice)
            return unauthorized_response("Invalid email or password")
        
        # Generate token
        token = generate_token(user['_id'], user['email'], user.get('role', 'user'))
        
        # Return user info and token
        user_response = {
            "_id": user['_id'],
            "email": user['email'],
            "name": user.get('name', ''),
            "role": user.get('role', 'user'),
            "token": token
        }
        
        return success_response(user_response, 200)
        
    except Exception as e:
        logger.error(f"Error logging in user: {str(e)}")
        return error_response("Failed to authenticate", 500, str(e))
