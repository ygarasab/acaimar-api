import azure.functions as func
import logging
import json
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from shared.auth import get_token_from_request, verify_token

logger = logging.getLogger(__name__)


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
        
        token = get_token_from_request(req)
        
        if not token:
            return func.HttpResponse(
                json.dumps({"error": "Token required"}),
                status_code=401,
                mimetype="application/json",
                headers={"Access-Control-Allow-Origin": "*"}
            )
        
        payload = verify_token(token)
        
        if not payload:
            return func.HttpResponse(
                json.dumps({"error": "Invalid or expired token"}),
                status_code=401,
                mimetype="application/json",
                headers={"Access-Control-Allow-Origin": "*"}
            )
        
        # Return user info from token
        user_info = {
            "user_id": payload.get('user_id'),
            "email": payload.get('email'),
            "role": payload.get('role'),
            "valid": True
        }
        
        return func.HttpResponse(
            json.dumps(user_info, ensure_ascii=False),
            status_code=200,
            mimetype="application/json",
            headers={"Access-Control-Allow-Origin": "*"}
        )
    except Exception as e:
        logger.error(f"Error verifying token: {str(e)}")
        return func.HttpResponse(
            json.dumps({"error": "Failed to verify token", "details": str(e)}),
            status_code=500,
            mimetype="application/json"
        )
