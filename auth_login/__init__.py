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

# Store import status (mirror health endpoint behavior)
_import_errors = []

# Bootstrap shared robustness helpers (safe imports + fallback responses)
try:
    from shared.function_bootstrap import (
        ensure_app_root_on_syspath,
        get_response_fns,
        maybe_attach_import_errors,
        safe_import,
    )
except Exception:
    # Make sure app root is on sys.path so shared imports work
    parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if parent_dir not in sys.path:
        sys.path.insert(0, parent_dir)
    from shared.function_bootstrap import (
        ensure_app_root_on_syspath,
        get_response_fns,
        maybe_attach_import_errors,
        safe_import,
    )

ensure_app_root_on_syspath(__file__, logger=logger)
responses = get_response_fns(logger=logger, errors=_import_errors)
error_response = responses.error_response
success_response = responses.success_response
method_not_allowed_response = responses.method_not_allowed_response
unauthorized_response = responses.unauthorized_response

# Critical imports for login. If these fail, we return 503 (but we don't crash import-time).
_, _auth_attrs = safe_import(
    "shared.auth",
    ["generate_token"],
    logger=logger,
    errors=_import_errors,
    label="generate_token",
)
generate_token = _auth_attrs.get("generate_token")

_, _service_attrs = safe_import(
    "shared.services",
    ["authenticate_user"],
    logger=logger,
    errors=_import_errors,
    label="authenticate_user",
)
authenticate_user = _service_attrs.get("authenticate_user")

# Validators are nice-to-have; provide lightweight fallbacks if missing.
def _validate_required_fields_fallback(data: dict, fields: list[str]):
    if not isinstance(data, dict):
        return False, "Request body must be a JSON object"
    for f in fields:
        if f not in data or data[f] is None or data[f] == "":
            return False, f"Field '{f}' is required"
    return True, None

def _sanitize_email_fallback(email: str) -> str:
    return email.lower().strip() if isinstance(email, str) else ""

_, _validator_attrs = safe_import(
    "shared.validators",
    ["validate_required_fields", "sanitize_email"],
    logger=logger,
    errors=_import_errors,
    label="validators",
)
validate_required_fields = _validator_attrs.get("validate_required_fields") or _validate_required_fields_fallback
sanitize_email = _validator_attrs.get("sanitize_email") or _sanitize_email_fallback


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

        # Only fail if *critical* imports are missing. Response/validator imports can fall back.
        if not generate_token or not authenticate_user:
            payload = maybe_attach_import_errors(
                {
                    "error": "Login service unavailable (server import errors)",
                },
                _import_errors,
            )
            return func.HttpResponse(
                json.dumps(payload, ensure_ascii=False),
                status_code=503,
                mimetype="application/json",
                headers={"Access-Control-Allow-Origin": "*"},
            )
        
        if req.method != 'POST':
            return method_not_allowed_response()
        
        try:
            req_body = req.get_json()
        except Exception as json_error:
            return error_response("Invalid JSON body", 400, str(json_error))
        
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
        return error_response("Failed to authenticate", 500, error_msg)
