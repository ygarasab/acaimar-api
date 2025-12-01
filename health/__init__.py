import azure.functions as func
import logging
import json
import sys
import os
from datetime import datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from shared.db_connection import get_mongo_client, get_database

logger = logging.getLogger(__name__)


def main(req: func.HttpRequest) -> func.HttpResponse:
    """
    GET /api/health
    Health check endpoint - returns API and database status
    """
    health_status = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "AÇAIMAR API",
        "version": "1.0.0",
        "checks": {
            "api": {
                "status": "ok",
                "message": "API is running"
            },
            "database": {
                "status": "unknown",
                "message": "Not checked"
            }
        }
    }
    
    http_status = 200
    
    # Check MongoDB connection
    try:
        client = get_mongo_client()
        db = get_database()
        
        # Ping the database
        client.admin.command('ping')
        
        # Get database stats
        db_stats = db.command("dbStats")
        
        health_status["checks"]["database"] = {
            "status": "ok",
            "message": "Database connection successful",
            "database": db.name,
            "collections": db_stats.get("collections", 0),
            "dataSize": db_stats.get("dataSize", 0)
        }
        
        logger.info("Health check: All systems operational")
        
    except Exception as e:
        health_status["status"] = "degraded"
        health_status["checks"]["database"] = {
            "status": "error",
            "message": f"Database connection failed: {str(e)}"
        }
        http_status = 503  # Service Unavailable
        logger.error(f"Health check: Database connection failed - {str(e)}")
    
    return func.HttpResponse(
        json.dumps(health_status, indent=2, ensure_ascii=False),
        status_code=http_status,
        mimetype="application/json",
        headers={
            "Access-Control-Allow-Origin": "*",
            "Cache-Control": "no-cache"
        }
    )
