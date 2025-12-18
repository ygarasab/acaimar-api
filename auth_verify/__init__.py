import azure.functions as func
import logging
import json
import sys
import os
import traceback

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
unauthorized_response = responses.unauthorized_response

_, _auth_attrs = safe_import(
    "shared.auth",
    ["get_token_from_request", "verify_token"],
    logger=logger,
    errors=_import_errors,
    label="auth functions",
)
get_token_from_request = _auth_attrs.get("get_token_from_request")
verify_token = _auth_attrs.get("verify_token")


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

        if _import_errors or not get_token_from_request or not verify_token:
            payload = maybe_attach_import_errors(
                {"error": "Auth verify service unavailable (import errors)"}, _import_errors
            )
            return func.HttpResponse(
                json.dumps(payload, ensure_ascii=False),
                status_code=503,
                mimetype="application/json",
                headers={"Access-Control-Allow-Origin": "*"},
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
