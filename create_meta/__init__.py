import azure.functions as func
import logging
import json
import sys
import os
import traceback

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
require_auth = safe_require_auth(logger=logger, errors=_import_errors)

_, _db_attrs = safe_import(
    "shared.db_connection",
    ["get_collection"],
    logger=logger,
    errors=_import_errors,
    label="db connection",
)
get_collection = _db_attrs.get("get_collection")


@require_auth(require_role='admin')
def main(req: func.HttpRequest) -> func.HttpResponse:
    """
    POST /api/metas
    Create a new meta
    """
    try:
        if _import_errors or not get_collection:
            payload = maybe_attach_import_errors(
                {"error": "Create meta service unavailable (import errors)"}, _import_errors
            )
            return func.HttpResponse(
                json.dumps(payload, ensure_ascii=False),
                status_code=503,
                mimetype="application/json",
                headers={"Access-Control-Allow-Origin": "*"},
            )

        req_body = req.get_json()
        
        if not req_body:
            return error_response("Request body is required", 400)
        
        # Validate required fields
        required_fields = ['titulo', 'descricao']
        missing_fields = [field for field in required_fields if field not in req_body]
        if missing_fields:
            return error_response(f"Missing required fields: {', '.join(missing_fields)}", 400)
        
        # Set default status if not provided
        if 'status' not in req_body:
            req_body['status'] = 'pendente'
        
        try:
            collection = get_collection('metas')
            result = collection.insert_one(req_body)
            
            # Retrieve the created document
            created_meta = collection.find_one({"_id": result.inserted_id})
            if not created_meta:
                return error_response("Meta was created but could not be retrieved", 500)
            
            created_meta['_id'] = str(created_meta['_id'])
            
            return success_response(created_meta, 201)
        except Exception as db_error:
            error_msg = str(db_error)
            error_trace = traceback.format_exc()
            logger.error(f"Database error creating meta: {error_msg}")
            logger.error(f"Traceback: {error_trace}")
            logger.error(f"Exception type: {type(db_error).__name__}")
            return error_response("Failed to create meta in database", 500, error_msg)
    except Exception as e:
        error_msg = str(e)
        error_trace = traceback.format_exc()
        logger.error(f"Error creating meta: {error_msg}")
        logger.error(f"Traceback: {error_trace}")
        logger.error(f"Exception type: {type(e).__name__}")
        return error_response("Failed to create meta", 500, error_msg)
