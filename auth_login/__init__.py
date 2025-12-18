import azure.functions as func
import logging
import sys
import os
import traceback
import json

# Common robustness helpers (used for debug-gated import error reporting)
try:
    from shared.function_bootstrap import maybe_attach_import_errors, _debug_import_errors_enabled
except Exception:
    try:
        parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        if parent_dir not in sys.path:
            sys.path.insert(0, parent_dir)
        from shared.function_bootstrap import maybe_attach_import_errors, _debug_import_errors_enabled
    except Exception:
        maybe_attach_import_errors = None  # Fallback to old behavior if bootstrap can't be imported
        _debug_import_errors_enabled = None

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

# Store import status (mirror health endpoint behavior)
_import_errors = []
_auth_functions_available = False
_response_functions_available = False
_validators_available = False
_services_available = False

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
    _import_errors.append(error_msg)

# Import shared modules with error handling - don't raise, store errors
try:
    from shared.auth import generate_token
    logger.info("Successfully imported generate_token")
    print("INFO: Successfully imported generate_token")
    _auth_functions_available = True
except ImportError as e:
    error_msg = f"Failed to import generate_token: {str(e)}"
    logger.error(error_msg, exc_info=True)
    print(f"ERROR: {error_msg}")
    print(f"ERROR: sys.path: {sys.path}")
    _import_errors.append(error_msg)
except Exception as e:
    error_msg = f"Unexpected error importing generate_token: {str(e)}"
    logger.error(error_msg, exc_info=True)
    print(f"ERROR: {error_msg}")
    print(f"ERROR: {traceback.format_exc()}")
    _import_errors.append(error_msg)

try:
    # Use the same response module import pattern as health
    from shared.utils.responses import (
        error_response,
        success_response,
        method_not_allowed_response,
        unauthorized_response
    )
    logger.info("Successfully imported response utilities")
    print("INFO: Successfully imported response utilities")
    _response_functions_available = True
except ImportError as e:
    error_msg = f"Failed to import response utilities: {str(e)}"
    logger.error(error_msg, exc_info=True)
    print(f"ERROR: {error_msg}")
    print(f"ERROR: sys.path: {sys.path}")
    _import_errors.append(error_msg)
except Exception as e:
    error_msg = f"Unexpected error importing response utilities: {str(e)}"
    logger.error(error_msg, exc_info=True)
    print(f"ERROR: {error_msg}")
    print(f"ERROR: {traceback.format_exc()}")
    _import_errors.append(error_msg)

try:
    from shared.validators import (
        validate_required_fields,
        sanitize_email
    )
    logger.info("Successfully imported validators")
    print("INFO: Successfully imported validators")
    _validators_available = True
except ImportError as e:
    error_msg = f"Failed to import validators: {str(e)}"
    logger.error(error_msg, exc_info=True)
    print(f"ERROR: {error_msg}")
    _import_errors.append(error_msg)
except Exception as e:
    error_msg = f"Unexpected error importing validators: {str(e)}"
    logger.error(error_msg, exc_info=True)
    print(f"ERROR: {error_msg}")
    print(f"ERROR: {traceback.format_exc()}")
    _import_errors.append(error_msg)

try:
    from shared.services import authenticate_user
    logger.info("Successfully imported authenticate_user")
    print("INFO: Successfully imported authenticate_user")
    _services_available = True
except ImportError as e:
    error_msg = f"Failed to import authenticate_user: {str(e)}"
    logger.error(error_msg, exc_info=True)
    print(f"ERROR: {error_msg}")
    _import_errors.append(error_msg)
except Exception as e:
    error_msg = f"Unexpected error importing authenticate_user: {str(e)}"
    logger.error(error_msg, exc_info=True)
    print(f"ERROR: {error_msg}")
    print(f"ERROR: {traceback.format_exc()}")
    _import_errors.append(error_msg)


def main(req: func.HttpRequest) -> func.HttpResponse:
    """
    POST /api/auth/login
    Authenticate user and return JWT token
    """
    print(f"INFO: auth_login function called, method: {req.method}")
    logger.info(f"auth_login function called, method: {req.method}")
    try:
        # If imports failed, return error immediately (mirror health endpoint behavior)
        if _import_errors:
            error_details = "; ".join(_import_errors)
            print(f"ERROR: Import errors detected: {error_details}")
            logger.error(f"Import errors: {error_details}")

            # Try to use error_response if available, otherwise fall back to basic HttpResponse
            if _response_functions_available:
                try:
                    return error_response(
                        "Login failed due to server import errors",
                        503,
                        error_details
                        if (_debug_import_errors_enabled and _debug_import_errors_enabled())
                        else None
                    )
                except Exception:
                    pass

            payload = {
                "error": "Login failed due to server import errors",
                "python_version": sys.version,
            }
            if maybe_attach_import_errors:
                payload = maybe_attach_import_errors(payload, _import_errors)
            else:
                payload["import_errors"] = _import_errors
                payload["details"] = error_details

            return func.HttpResponse(
                json.dumps(payload, ensure_ascii=False),
                status_code=503,
                mimetype="application/json",
                headers={"Access-Control-Allow-Origin": "*"}
            )

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
            if _response_functions_available:
                return method_not_allowed_response()
            return func.HttpResponse(
                json.dumps({"error": "Method not allowed"}, ensure_ascii=False),
                status_code=405,
                mimetype="application/json",
                headers={"Access-Control-Allow-Origin": "*"}
            )
        
        try:
            req_body = req.get_json()
        except Exception as json_error:
            if _response_functions_available:
                return error_response("Invalid JSON body", 400, str(json_error))
            return func.HttpResponse(
                json.dumps({"error": "Invalid JSON body", "details": str(json_error)}, ensure_ascii=False),
                status_code=400,
                mimetype="application/json",
                headers={"Access-Control-Allow-Origin": "*"}
            )
        
        if not req_body:
            if _response_functions_available:
                return error_response("Request body is required", 400)
            return func.HttpResponse(
                json.dumps({"error": "Request body is required"}, ensure_ascii=False),
                status_code=400,
                mimetype="application/json",
                headers={"Access-Control-Allow-Origin": "*"}
            )
        
        # Validate required fields
        is_valid, error_msg = validate_required_fields(req_body, ['email', 'password'])
        if not is_valid:
            if _response_functions_available:
                return error_response(error_msg, 400)
            return func.HttpResponse(
                json.dumps({"error": error_msg}, ensure_ascii=False),
                status_code=400,
                mimetype="application/json",
                headers={"Access-Control-Allow-Origin": "*"}
            )
        
        email = sanitize_email(req_body['email'])
        password = req_body['password']
        
        # Authenticate user
        user = authenticate_user(email, password)
        
        if not user:
            # Don't reveal if user exists or not (security best practice)
            if _response_functions_available:
                return unauthorized_response("Invalid email or password")
            return func.HttpResponse(
                json.dumps({"error": "Invalid email or password"}, ensure_ascii=False),
                status_code=401,
                mimetype="application/json",
                headers={"Access-Control-Allow-Origin": "*"}
            )
        
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
        
        if _response_functions_available:
            return success_response(user_response, 200)
        return func.HttpResponse(
            json.dumps(user_response, ensure_ascii=False),
            status_code=200,
            mimetype="application/json",
            headers={"Access-Control-Allow-Origin": "*"}
        )
        
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
            if _response_functions_available:
                return error_response("Failed to authenticate", 500, error_msg)
            raise Exception("response utilities unavailable")
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
