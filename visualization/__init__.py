import azure.functions as func
import logging
import json
import sys
import os
import traceback
from datetime import datetime, timedelta
import base64
from io import BytesIO

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
not_found_response = responses.not_found_response

_, _db_attrs = safe_import(
    "shared.db_connection",
    ["get_collection"],
    logger=logger,
    errors=_import_errors,
    label="db connection",
)
get_collection = _db_attrs.get("get_collection")


def _load_plotting_libs():
    """
    Lazy-load heavy plotting dependencies. Keeps cold starts lighter for non-visualization endpoints.
    Returns (pd, plt).
    Raises ImportError/Exception if libs can't be loaded.
    """
    import pandas as pd  # noqa: F401

    import matplotlib

    # Ensure non-interactive backend (safe to ignore if backend already set)
    try:
        matplotlib.use("Agg")
    except Exception:
        pass

    import matplotlib.pyplot as plt  # noqa: F401

    # Optional styling
    try:
        import seaborn as sns

        sns.set_style("whitegrid")
    except Exception:
        sns = None  # noqa: F841

    plt.rcParams["figure.figsize"] = (10, 6)
    plt.rcParams["font.size"] = 10

    return pd, plt


def generate_chart_base64(fig, plt):
    """Convert matplotlib figure to base64 string"""
    buffer = BytesIO()
    fig.savefig(buffer, format='png', dpi=100, bbox_inches='tight')
    buffer.seek(0)
    image_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
    plt.close(fig)
    return image_base64


def chart_metas_status(req: func.HttpRequest) -> func.HttpResponse:
    """
    GET /api/visualization/metas-status
    Generate a chart showing the distribution of metas by status
    """
    try:
        if _import_errors or not get_collection:
            payload = maybe_attach_import_errors(
                {"error": "Visualization service unavailable (import errors)"}, _import_errors
            )
            return func.HttpResponse(
                json.dumps(payload, ensure_ascii=False),
                status_code=503,
                mimetype="application/json",
                headers={"Access-Control-Allow-Origin": "*"},
            )

        try:
            pd, plt = _load_plotting_libs()
        except Exception as lib_error:
            payload = maybe_attach_import_errors(
                {"error": "Visualization dependencies unavailable", "details": str(lib_error)},
                _import_errors,
            )
            return func.HttpResponse(
                json.dumps(payload, ensure_ascii=False),
                status_code=503,
                mimetype="application/json",
                headers={"Access-Control-Allow-Origin": "*"},
            )

        collection = get_collection('metas')
        metas = list(collection.find({}))
        
        if not metas:
            return not_found_response("No metas data available for visualization")
        
        # Count metas by status
        df = pd.DataFrame(metas)
        status_counts = df['status'].value_counts()
        
        # Create pie chart
        fig, ax = plt.subplots(figsize=(8, 8))
        colors = ['#667eea', '#764ba2', '#f093fb', '#4facfe']
        ax.pie(status_counts.values, labels=status_counts.index, autopct='%1.1f%%',
               colors=colors[:len(status_counts)], startangle=90)
        ax.set_title('Distribuição de Metas por Status', fontsize=14, fontweight='bold')
        
        chart_base64 = generate_chart_base64(fig, plt)
        
        return success_response({
            "chart": f"data:image/png;base64,{chart_base64}",
            "data": status_counts.to_dict()
        }, 200)
    except Exception as e:
        error_msg = str(e)
        error_trace = traceback.format_exc()
        logger.error(f"Error generating metas status chart: {error_msg}")
        logger.error(f"Traceback: {error_trace}")
        logger.error(f"Exception type: {type(e).__name__}")
        return error_response("Failed to generate metas status chart", 500, error_msg)


def chart_sensor_data(req: func.HttpRequest) -> func.HttpResponse:
    """
    GET /api/visualization/sensor-data
    Generate charts for sensor data visualization
    Supports query parameters: days (number of days to visualize)
    """
    try:
        if _import_errors or not get_collection:
            payload = maybe_attach_import_errors(
                {"error": "Visualization service unavailable (import errors)"}, _import_errors
            )
            return func.HttpResponse(
                json.dumps(payload, ensure_ascii=False),
                status_code=503,
                mimetype="application/json",
                headers={"Access-Control-Allow-Origin": "*"},
            )

        try:
            pd, plt = _load_plotting_libs()
        except Exception as lib_error:
            payload = maybe_attach_import_errors(
                {"error": "Visualization dependencies unavailable", "details": str(lib_error)},
                _import_errors,
            )
            return func.HttpResponse(
                json.dumps(payload, ensure_ascii=False),
                status_code=503,
                mimetype="application/json",
                headers={"Access-Control-Allow-Origin": "*"},
            )

        # Get query parameters
        days = int(req.params.get('days', 7))
        
        collection = get_collection('sensor_data')
        
        # Calculate date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        # Query sensor data
        query = {
            "timestamp": {
                "$gte": start_date.isoformat(),
                "$lte": end_date.isoformat()
            }
        }
        
        sensor_data = list(collection.find(query).sort("timestamp", 1))
        
        if not sensor_data:
            # Return sample data structure if no data exists
            return success_response({
                "message": "No sensor data available",
                "sample_structure": {
                    "timestamp": "ISO format datetime",
                    "temperature": "float",
                    "humidity": "float",
                    "soil_moisture": "float",
                    "light_intensity": "float"
                }
            }, 200)
        
        # Convert to DataFrame
        df = pd.DataFrame(sensor_data)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        
        # Create subplots for different metrics
        fig, axes = plt.subplots(2, 2, figsize=(14, 10))
        fig.suptitle(f'Dados de Sensores - Últimos {days} dias', fontsize=16, fontweight='bold')
        
        metrics = [
            ('temperature', 'Temperatura (°C)', axes[0, 0]),
            ('humidity', 'Umidade (%)', axes[0, 1]),
            ('soil_moisture', 'Umidade do Solo (%)', axes[1, 0]),
            ('light_intensity', 'Intensidade de Luz (lux)', axes[1, 1])
        ]
        
        charts_data = {}
        
        for metric, title, ax in metrics:
            if metric in df.columns:
                ax.plot(df['timestamp'], df[metric], linewidth=2, color='#667eea')
                ax.set_title(title, fontweight='bold')
                ax.set_xlabel('Data')
                ax.set_ylabel(title.split('(')[0].strip())
                ax.grid(True, alpha=0.3)
                ax.tick_params(axis='x', rotation=45)
                
                # Calculate statistics
                charts_data[metric] = {
                    "mean": float(df[metric].mean()),
                    "min": float(df[metric].min()),
                    "max": float(df[metric].max()),
                    "std": float(df[metric].std())
                }
        
        plt.tight_layout()
        chart_base64 = generate_chart_base64(fig, plt)
        
        return success_response({
            "chart": f"data:image/png;base64,{chart_base64}",
            "statistics": charts_data,
            "data_points": len(df)
        }, 200)
    except ValueError as ve:
        error_msg = str(ve)
        error_trace = traceback.format_exc()
        logger.error(f"Invalid query parameter: {error_msg}")
        logger.error(f"Traceback: {error_trace}")
        return error_response("Invalid query parameter. 'days' must be a positive integer", 400, error_msg)
    except Exception as e:
        error_msg = str(e)
        error_trace = traceback.format_exc()
        logger.error(f"Error generating sensor data chart: {error_msg}")
        logger.error(f"Traceback: {error_trace}")
        logger.error(f"Exception type: {type(e).__name__}")
        return error_response("Failed to generate sensor data chart", 500, error_msg)


def main(req: func.HttpRequest) -> func.HttpResponse:
    """
    Main router for visualization endpoints
    """
    route = req.route_params.get('chart_type', '')
    
    try:
        if route == 'metas-status':
            return chart_metas_status(req)
        elif route == 'sensor-data':
            return chart_sensor_data(req)
        else:
            return error_response(
                f"Invalid chart type '{route}'",
                400,
                f"Available chart types: metas-status, sensor-data"
            )
    except Exception as e:
        error_msg = str(e)
        error_trace = traceback.format_exc()
        logger.error(f"Error in visualization router: {error_msg}")
        logger.error(f"Traceback: {error_trace}")
        logger.error(f"Exception type: {type(e).__name__}")
        return error_response("Failed to process visualization request", 500, error_msg)
