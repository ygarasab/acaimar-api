import azure.functions as func
import logging
import json
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from shared.auth import get_token_from_request, verify_token
from shared.utils.responses import error_response, success_response, unauthorized_response

logger = logging.getLogger(__name__)


def main(req: func.HttpRequest) -> func.HttpResponse:
    """
    GET /api/auth/verify
    Verify JWT token and return user info
    """
    try:
        if req.method == 'OPTIONS':
            return func.HttpResponse(
                "",
                status_code=200,
                headers={
                    "Access-Control-Allow-Origin": "*",
                    "Access-Control-Allow-Methods": "GET, OPTIONS",
                    "Access-Control-Allow-Headers": "Authorization"
                }
            )
        
        token = get_token_from_request(req)
        
        if not token:
            return unauthorized_response("Token required. Please provide a valid JWT token in the Authorization header.")
        
        payload = verify_token(token)
        
        if not payload:
            return unauthorized_response("Invalid or expired token. Please login again to get a new token.")
        
        # Return user info from token
        user_info = {
            "user_id": payload.get('user_id'),
            "email": payload.get('email'),
            "role": payload.get('role'),
            "valid": True
        }
        
        return success_response(user_info, 200)
    except Exception as e:
        logger.error(f"Error verifying token: {str(e)}", exc_info=True)
        return error_response("Failed to verify token", 500, str(e))
