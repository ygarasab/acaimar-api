import azure.functions as func
import logging
import sys
import os
import traceback
import json

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Bootstrap shared robustness helpers (safe imports + fallback responses + safe auth decorator)
_import_errors = []
try:
    from shared.function_bootstrap import (
        ensure_app_root_on_syspath,
        get_response_fns,
        maybe_attach_import_errors,
        safe_import,
        safe_require_auth,
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
        safe_require_auth,
    )

ensure_app_root_on_syspath(__file__, logger=logger)
responses = get_response_fns(logger=logger, errors=_import_errors)
error_response = responses.error_response
success_response = responses.success_response
method_not_allowed_response = responses.method_not_allowed_response
require_auth = safe_require_auth(logger=logger, errors=_import_errors)

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
    ["get_all_users", "create_user", "user_exists"],
    logger=logger,
    errors=_import_errors,
    label="user services",
)
get_all_users = _service_attrs.get("get_all_users")
create_user_db = _service_attrs.get("create_user")
user_exists = _service_attrs.get("user_exists")


@require_auth(require_role='admin')
def main(req: func.HttpRequest) -> func.HttpResponse:
    """
    GET /api/users - Retrieve all users
    POST /api/users - Create a new user
    """
    try:
        if _import_errors or not all(
            [
                validate_required_fields,
                validate_email,
                validate_password,
                sanitize_email,
                sanitize_string,
                get_all_users,
                create_user_db,
                user_exists,
            ]
        ):
            payload = maybe_attach_import_errors(
                {"error": "Users service unavailable (import errors)"}, _import_errors
            )
            return func.HttpResponse(
                json.dumps(payload, ensure_ascii=False),
                status_code=503,
                mimetype="application/json",
                headers={"Access-Control-Allow-Origin": "*"},
            )

        if req.method == 'GET':
            return get_users(req)
        elif req.method == 'POST':
            return create_user(req)
        else:
            return method_not_allowed_response()
    except Exception as e:
        error_msg = str(e)
        error_trace = traceback.format_exc()
        logger.error(f"Error in users endpoint: {error_msg}")
        logger.error(f"Traceback: {error_trace}")
        logger.error(f"Exception type: {type(e).__name__}")
        return error_response("Internal server error", 500, error_msg)


def get_users(req: func.HttpRequest) -> func.HttpResponse:
    """GET /api/users - Retrieve all users"""
    try:
        users = get_all_users()
        return success_response(users, 200)
    except Exception as e:
        error_msg = str(e)
        error_trace = traceback.format_exc()
        logger.error(f"Error retrieving users: {error_msg}")
        logger.error(f"Traceback: {error_trace}")
        logger.error(f"Exception type: {type(e).__name__}")
        return error_response("Failed to retrieve users", 500, error_msg)


def create_user(req: func.HttpRequest) -> func.HttpResponse:
    """POST /api/users - Create a new user"""
    req_body = req.get_json()
    
    # Validate request body exists
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
    role = req_body.get('role', 'user')
    
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
        return success_response(user, 201)
    except ValueError as e:
        error_msg = str(e)
        error_trace = traceback.format_exc()
        logger.error(f"ValueError creating user: {error_msg}")
        logger.error(f"Traceback: {error_trace}")
        return error_response(error_msg, 409)
    except Exception as e:
        error_msg = str(e)
        error_trace = traceback.format_exc()
        logger.error(f"Error creating user: {error_msg}")
        logger.error(f"Traceback: {error_trace}")
        logger.error(f"Exception type: {type(e).__name__}")
        return error_response("Failed to create user", 500, error_msg)
