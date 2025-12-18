import azure.functions as func
import logging
import sys
import os
import traceback
import json

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Bootstrap shared robustness helpers (safe imports + fallback responses)
_import_errors = []
try:
    from shared.function_bootstrap import (
        ensure_app_root_on_syspath,
        get_response_fns,
        maybe_attach_import_errors,
        safe_import,
    )
except Exception:
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

_, _auth_attrs = safe_import(
    "shared.auth",
    ["generate_token"],
    logger=logger,
    errors=_import_errors,
    label="generate_token",
)
generate_token = _auth_attrs.get("generate_token")

_, _validator_attrs = safe_import(
    "shared.validators",
    [
        "validate_required_fields",
        "validate_email",
        "validate_password",
        "sanitize_email",
        "sanitize_string",
    ],
    logger=logger,
    errors=_import_errors,
    label="validators",
)
validate_required_fields = _validator_attrs.get("validate_required_fields")
validate_email = _validator_attrs.get("validate_email")
validate_password = _validator_attrs.get("validate_password")
sanitize_email = _validator_attrs.get("sanitize_email")
sanitize_string = _validator_attrs.get("sanitize_string")

_, _service_attrs = safe_import(
    "shared.services",
    ["create_user", "user_exists"],
    logger=logger,
    errors=_import_errors,
    label="user services",
)
create_user_db = _service_attrs.get("create_user")
user_exists = _service_attrs.get("user_exists")


def main(req: func.HttpRequest) -> func.HttpResponse:
    """
    POST /api/auth/register
    Register a new user
    """
    try:
        if _import_errors or not all(
            [
                generate_token,
                validate_required_fields,
                validate_email,
                validate_password,
                sanitize_email,
                sanitize_string,
                create_user_db,
                user_exists,
            ]
        ):
            payload = maybe_attach_import_errors(
                {"error": "Registration service unavailable (import errors)"}, _import_errors
            )
            return func.HttpResponse(
                json.dumps(payload, ensure_ascii=False),
                status_code=503,
                mimetype="application/json",
                headers={"Access-Control-Allow-Origin": "*"},
            )

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
            logger.error(f"ValueError creating user: {str(e)}", exc_info=True)
            return error_response(str(e), 409)
        except Exception as e:
            error_msg = str(e)
            error_trace = traceback.format_exc()
            logger.error(f"Error creating user: {error_msg}")
            logger.error(f"Traceback: {error_trace}")
            logger.error(f"Exception type: {type(e).__name__}")
            return error_response("Failed to register user", 500, error_msg)
            
    except Exception as e:
        error_msg = str(e)
        error_trace = traceback.format_exc()
        logger.error(f"Error registering user: {error_msg}")
        logger.error(f"Traceback: {error_trace}")
        logger.error(f"Exception type: {type(e).__name__}")
        return error_response("Failed to register user", 500, error_msg)
