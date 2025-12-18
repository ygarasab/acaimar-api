"""
Common robustness helpers for Azure Functions entrypoints.

Goals:
- Avoid import-time crashes in function modules.
- Standardize safe-import behavior + consistent fallback HttpResponses.
- Provide a safe `require_auth` decorator factory that degrades gracefully if auth can't import.
"""

from __future__ import annotations

import importlib
import json
import logging
import os
import sys
import traceback
from dataclasses import dataclass
from typing import Any, Callable, Dict, Iterable, Optional, Tuple

import azure.functions as func


def ensure_app_root_on_syspath(current_file: str, logger: Optional[logging.Logger] = None) -> Tuple[Optional[str], Optional[str]]:
    """
    Ensure the Azure Functions app root (parent of the function folder) is on sys.path.
    Returns (app_root, error_msg).
    """
    try:
        app_root = os.path.dirname(os.path.dirname(os.path.abspath(current_file)))
        if app_root and app_root not in sys.path:
            # Put first so shared imports resolve consistently across functions.
            sys.path.insert(0, app_root)
        return app_root, None
    except Exception as e:
        msg = f"Error setting up sys.path: {str(e)}"
        if logger:
            logger.error(msg, exc_info=True)
        return None, msg


def _debug_import_errors_enabled() -> bool:
    # Compatibility: health uses HEALTH_DEBUG; make this work repo-wide too.
    v = (
        os.environ.get("DEBUG_IMPORT_ERRORS", "")
        or os.environ.get("FUNC_DEBUG_IMPORT_ERRORS", "")
        or os.environ.get("HEALTH_DEBUG", "")
    ).lower()
    return v in ("1", "true", "yes", "on")


def fallback_json_response(data: Any, status_code: int = 200, headers: Optional[Dict[str, str]] = None) -> func.HttpResponse:
    h = {"Access-Control-Allow-Origin": "*"}
    if headers:
        h.update(headers)
    return func.HttpResponse(
        json.dumps(data, ensure_ascii=False),
        status_code=status_code,
        mimetype="application/json",
        headers=h,
    )


def fallback_error_response(error: str, status_code: int = 400, details: Optional[str] = None) -> func.HttpResponse:
    payload: Dict[str, Any] = {"error": error}
    if details:
        payload["details"] = details
    return fallback_json_response(payload, status_code=status_code)


def safe_import(
    module_path: str,
    attr_names: Optional[Iterable[str]] = None,
    *,
    logger: Optional[logging.Logger] = None,
    errors: Optional[list[str]] = None,
    label: Optional[str] = None,
) -> Tuple[Optional[Any], Dict[str, Any]]:
    """
    Import a module (and optionally attributes) without raising.

    Returns:
    - module (or None on failure)
    - attrs dict (empty on failure or if attr_names is None)
    """
    attrs: Dict[str, Any] = {}
    try:
        mod = importlib.import_module(module_path)
        if attr_names:
            for name in attr_names:
                attrs[name] = getattr(mod, name)
        return mod, attrs
    except Exception as e:
        msg = f"Failed to import {label or module_path}: {str(e)}"
        if logger:
            logger.error(msg, exc_info=True)
        if errors is not None:
            errors.append(msg)
        return None, {}


@dataclass(frozen=True)
class ResponseFns:
    json_response: Callable[[Any, int], func.HttpResponse]
    error_response: Callable[[str, int, Optional[str]], func.HttpResponse]
    success_response: Callable[[Dict[str, Any], int], func.HttpResponse]
    method_not_allowed_response: Callable[[], func.HttpResponse]
    not_found_response: Callable[[str], func.HttpResponse]
    unauthorized_response: Callable[[str], func.HttpResponse]
    forbidden_response: Callable[[str], func.HttpResponse]


def get_response_fns(logger: Optional[logging.Logger] = None, errors: Optional[list[str]] = None) -> ResponseFns:
    """
    Try to use shared response utilities; otherwise return fallbacks.
    """
    _, attrs = safe_import(
        "shared.utils.responses",
        [
            "json_response",
            "error_response",
            "success_response",
            "method_not_allowed_response",
            "not_found_response",
            "unauthorized_response",
            "forbidden_response",
        ],
        logger=logger,
        errors=errors,
        label="response utilities",
    )

    if attrs:
        return ResponseFns(
            json_response=attrs["json_response"],
            error_response=attrs["error_response"],
            success_response=attrs["success_response"],
            method_not_allowed_response=attrs["method_not_allowed_response"],
            not_found_response=attrs["not_found_response"],
            unauthorized_response=attrs["unauthorized_response"],
            forbidden_response=attrs["forbidden_response"],
        )

    # Fallback implementations
    return ResponseFns(
        json_response=lambda data, status_code=200: fallback_json_response(data, status_code),
        error_response=lambda error, status_code=400, details=None: fallback_error_response(error, status_code, details),
        success_response=lambda data, status_code=200: fallback_json_response(data, status_code),
        method_not_allowed_response=lambda: fallback_error_response("Method not allowed", 405),
        not_found_response=lambda resource="Resource": fallback_error_response(f"{resource} not found", 404),
        unauthorized_response=lambda message="Authentication required": fallback_error_response(message, 401),
        forbidden_response=lambda message="Insufficient permissions": fallback_error_response(message, 403),
    )


def safe_require_auth(
    *,
    logger: Optional[logging.Logger] = None,
    errors: Optional[list[str]] = None,
) -> Callable[[Optional[str]], Callable[[Callable[..., func.HttpResponse]], Callable[..., func.HttpResponse]]]:
    """
    Return a `require_auth(require_role=...)` decorator factory.
    If `shared.auth` can't be imported, returns a decorator that responds with 503 instead of crashing at import time.
    """
    responses = get_response_fns(logger=logger, errors=errors)
    _, attrs = safe_import(
        "shared.auth",
        ["require_auth"],
        logger=logger,
        errors=errors,
        label="auth utilities",
    )

    require_auth_fn = attrs.get("require_auth")
    if require_auth_fn:
        return require_auth_fn

    def require_auth_fallback(require_role: Optional[str] = None):
        def decorator(handler):
            def wrapper(req: func.HttpRequest, *args, **kwargs):
                details = None
                if _debug_import_errors_enabled() and errors:
                    details = "; ".join(errors)
                return responses.error_response(
                    "Authentication system unavailable",
                    503,
                    details,
                )

            return wrapper

        return decorator

    return require_auth_fallback


def maybe_attach_import_errors(payload: Dict[str, Any], errors: list[str]) -> Dict[str, Any]:
    """
    Attach import errors to payload only when debug is enabled.
    """
    if _debug_import_errors_enabled() and errors:
        payload = dict(payload)
        payload["import_errors"] = errors
    return payload


