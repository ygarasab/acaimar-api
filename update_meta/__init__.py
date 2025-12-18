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
not_found_response = responses.not_found_response
require_auth = safe_require_auth(logger=logger, errors=_import_errors)

_, _db_attrs = safe_import(
    "shared.db_connection",
    ["get_collection"],
    logger=logger,
    errors=_import_errors,
    label="db connection",
)
get_collection = _db_attrs.get("get_collection")

_, _bson_attrs = safe_import(
    "bson",
    ["ObjectId"],
    logger=logger,
    errors=_import_errors,
    label="bson",
)
ObjectId = _bson_attrs.get("ObjectId")


@require_auth(require_role='admin')
def main(req: func.HttpRequest) -> func.HttpResponse:
    """
    PUT /api/metas/{id}
    Update an existing meta
    """
    try:
        if _import_errors or not get_collection or not ObjectId:
            payload = maybe_attach_import_errors(
                {"error": "Update meta service unavailable (import errors)"}, _import_errors
            )
            return func.HttpResponse(
                json.dumps(payload, ensure_ascii=False),
                status_code=503,
                mimetype="application/json",
                headers={"Access-Control-Allow-Origin": "*"},
            )

        meta_id = req.route_params.get('id')
        
        if not meta_id:
            return error_response("Meta ID is required in the route path", 400)
        
        req_body = req.get_json()
        
        if not req_body:
            return error_response("Request body is required", 400)
        
        if not req_body or len(req_body) == 0:
            return error_response("Request body cannot be empty. Provide at least one field to update", 400)
        
        # Remove _id from update body if present
        req_body.pop('_id', None)
        
        try:
            collection = get_collection('metas')
            result = collection.update_one(
                {"_id": ObjectId(meta_id)},
                {"$set": req_body}
            )
            
            if result.matched_count == 0:
                return not_found_response("Meta")
            
            # Retrieve the updated document
            updated_meta = collection.find_one({"_id": ObjectId(meta_id)})
            if not updated_meta:
                return error_response("Meta was updated but could not be retrieved", 500)
            
            updated_meta['_id'] = str(updated_meta['_id'])
            
            return success_response(updated_meta, 200)
        except ValueError as ve:
            error_msg = str(ve)
            error_trace = traceback.format_exc()
            logger.error(f"Invalid meta ID format: {error_msg}")
            logger.error(f"Traceback: {error_trace}")
            return error_response("Invalid meta ID format", 400, error_msg)
        except Exception as db_error:
            error_msg = str(db_error)
            error_trace = traceback.format_exc()
            logger.error(f"Database error updating meta: {error_msg}")
            logger.error(f"Traceback: {error_trace}")
            logger.error(f"Exception type: {type(db_error).__name__}")
            return error_response("Failed to update meta in database", 500, error_msg)
    except Exception as e:
        error_msg = str(e)
        error_trace = traceback.format_exc()
        logger.error(f"Error updating meta: {error_msg}")
        logger.error(f"Traceback: {error_trace}")
        logger.error(f"Exception type: {type(e).__name__}")
        return error_response("Failed to update meta", 500, error_msg)
