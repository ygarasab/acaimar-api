"""
Standardized HTTP response utilities
"""
import json
import azure.functions as func
from typing import Any, Dict, Optional


def json_response(data: Any, status_code: int = 200) -> func.HttpResponse:
    """
    Create a JSON HTTP response
    
    Args:
        data: Data to serialize as JSON
        status_code: HTTP status code
    
    Returns:
        HTTP response with JSON body
    """
    return func.HttpResponse(
        json.dumps(data, ensure_ascii=False),
        status_code=status_code,
        mimetype="application/json",
        headers={"Access-Control-Allow-Origin": "*"}
    )


def error_response(error: str, status_code: int = 400, details: Optional[str] = None) -> func.HttpResponse:
    """
    Create a standardized error response
    
    Args:
        error: Error message
        status_code: HTTP status code
        details: Optional detailed error information
    
    Returns:
        HTTP error response
    """
    response_data = {"error": error}
    if details:
        response_data["details"] = details
    
    return func.HttpResponse(
        json.dumps(response_data, ensure_ascii=False),
        status_code=status_code,
        mimetype="application/json",
        headers={"Access-Control-Allow-Origin": "*"}
    )


def success_response(data: Dict[str, Any], status_code: int = 200) -> func.HttpResponse:
    """
    Create a success response with data
    
    Args:
        data: Response data
        status_code: HTTP status code (default 200)
    
    Returns:
        HTTP success response
    """
    response = json_response(data, status_code)
    # Add CORS headers
    response.headers["Access-Control-Allow-Origin"] = "*"
    return response


def method_not_allowed_response() -> func.HttpResponse:
    """Create a 405 Method Not Allowed response"""
    return error_response("Method not allowed", 405)


def not_found_response(resource: str = "Resource") -> func.HttpResponse:
    """Create a 404 Not Found response"""
    return error_response(f"{resource} not found", 404)


def unauthorized_response(message: str = "Authentication required") -> func.HttpResponse:
    """Create a 401 Unauthorized response"""
    return error_response(message, 401)


def forbidden_response(message: str = "Insufficient permissions") -> func.HttpResponse:
    """Create a 403 Forbidden response"""
    return error_response(message, 403)
