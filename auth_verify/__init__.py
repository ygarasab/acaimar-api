import azure.functions as func
import logging
import json
import sys
import os
import traceback

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Add parent directory to path
try:
    parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sys.path.insert(0, parent_dir)
    logger.info(f"Added to sys.path: {parent_dir}")
except Exception as path_error:
    logger.error(f"Error setting up sys.path: {str(path_error)}", exc_info=True)

# Import shared modules with error handling
try:
    from shared.auth import get_token_from_request, verify_token
    logger.info("Successfully imported auth functions")
except ImportError as e:
    logger.error(f"Failed to import auth functions: {str(e)}", exc_info=True)
    raise

try:
    from shared.utils.responses import error_response, success_response, unauthorized_response
    logger.info("Successfully imported response utilities")
except ImportError as e:
    logger.error(f"Failed to import response utilities: {str(e)}", exc_info=True)
    raise


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
        error_msg = str(e)
        error_trace = traceback.format_exc()
        logger.error(f"Error verifying token: {error_msg}")
        logger.error(f"Traceback: {error_trace}")
        logger.error(f"Exception type: {type(e).__name__}")
        return error_response("Failed to verify token", 500, error_msg)
