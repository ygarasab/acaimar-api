import azure.functions as func
import logging
import sys
import os
import traceback
import json

# Configure logging - Azure Functions uses root logger
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Also use print - Azure Functions always logs print statements
print("=" * 50)
print("MODULE LOAD: auth_login/__init__.py")
print(f"Python version: {sys.version}")
print(f"Current directory: {os.getcwd()}")
print(f"__file__: {__file__}")
print("=" * 50)

# Add parent directory to path
try:
    parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sys.path.insert(0, parent_dir)
    logger.info(f"Added to sys.path: {parent_dir}")
    print(f"INFO: Added to sys.path: {parent_dir}")
    print(f"INFO: sys.path contents: {sys.path[:3]}")  # Print first 3 entries
except Exception as path_error:
    error_msg = f"Error setting up sys.path: {str(path_error)}"
    logger.error(error_msg, exc_info=True)
    print(f"ERROR: {error_msg}")
    print(f"ERROR: {traceback.format_exc()}")

# Import shared modules with error handling
import_errors = []
try:
    from shared.auth import generate_token
    logger.info("Successfully imported generate_token")
    print("INFO: Successfully imported generate_token")
except ImportError as e:
    error_msg = f"Failed to import generate_token: {str(e)}"
    logger.error(error_msg, exc_info=True)
    print(f"ERROR: {error_msg}")
    print(f"ERROR: sys.path: {sys.path}")
    import_errors.append(error_msg)
    raise

try:
    from shared.utils import (
        error_response,
        success_response,
        method_not_allowed_response,
        unauthorized_response
    )
    logger.info("Successfully imported response utilities")
    print("INFO: Successfully imported response utilities")
except ImportError as e:
    error_msg = f"Failed to import response utilities: {str(e)}"
    logger.error(error_msg, exc_info=True)
    print(f"ERROR: {error_msg}")
    print(f"ERROR: sys.path: {sys.path}")
    import_errors.append(error_msg)
    raise

try:
    from shared.validators import (
        validate_required_fields,
        sanitize_email
    )
    logger.info("Successfully imported validators")
    print("INFO: Successfully imported validators")
except ImportError as e:
    error_msg = f"Failed to import validators: {str(e)}"
    logger.error(error_msg, exc_info=True)
    print(f"ERROR: {error_msg}")
    import_errors.append(error_msg)
    raise

try:
    from shared.services import authenticate_user
    logger.info("Successfully imported authenticate_user")
    print("INFO: Successfully imported authenticate_user")
except ImportError as e:
    error_msg = f"Failed to import authenticate_user: {str(e)}"
    logger.error(error_msg, exc_info=True)
    print(f"ERROR: {error_msg}")
    import_errors.append(error_msg)
    raise


def main(req: func.HttpRequest) -> func.HttpResponse:
    """
    POST /api/auth/login
    Authenticate user and return JWT token
    """
    print(f"INFO: auth_login function called, method: {req.method}")
    logger.info(f"auth_login function called, method: {req.method}")
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
        error_msg = str(e)
        error_trace = traceback.format_exc()
        print(f"ERROR: Error logging in user: {error_msg}")
        print(f"ERROR: Traceback: {error_trace}")
        print(f"ERROR: Exception type: {type(e).__name__}")
        logger.error(f"Error logging in user: {error_msg}")
        logger.error(f"Traceback: {error_trace}")
        logger.error(f"Exception type: {type(e).__name__}")
        try:
            return error_response("Failed to authenticate", 500, error_msg)
        except:
            # Fallback if error_response also fails
            import json
            return func.HttpResponse(
                json.dumps({
                    "error": "Failed to authenticate",
                    "details": error_msg,
                    "traceback": error_trace
                }),
                status_code=500,
                mimetype="application/json"
            )
