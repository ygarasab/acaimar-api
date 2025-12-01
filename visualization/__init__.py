import azure.functions as func
import logging
import json
import sys
import os
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
import base64
from io import BytesIO
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
import seaborn as sns

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from shared.db_connection import get_collection

logger = logging.getLogger(__name__)

# Set style for better-looking charts
sns.set_style("whitegrid")
plt.rcParams['figure.figsize'] = (10, 6)
plt.rcParams['font.size'] = 10


def generate_chart_base64(fig):
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
        collection = get_collection('metas')
        metas = list(collection.find({}))
        
        if not metas:
            return func.HttpResponse(
                json.dumps({"error": "No data available for visualization"}),
                status_code=404,
                mimetype="application/json"
            )
        
        # Count metas by status
        df = pd.DataFrame(metas)
        status_counts = df['status'].value_counts()
        
        # Create pie chart
        fig, ax = plt.subplots(figsize=(8, 8))
        colors = ['#667eea', '#764ba2', '#f093fb', '#4facfe']
        ax.pie(status_counts.values, labels=status_counts.index, autopct='%1.1f%%',
               colors=colors[:len(status_counts)], startangle=90)
        ax.set_title('Distribuição de Metas por Status', fontsize=14, fontweight='bold')
        
        chart_base64 = generate_chart_base64(fig)
        
        return func.HttpResponse(
            json.dumps({
                "chart": f"data:image/png;base64,{chart_base64}",
                "data": status_counts.to_dict()
            }, ensure_ascii=False),
            status_code=200,
            mimetype="application/json",
            headers={"Access-Control-Allow-Origin": "*"}
        )
    except Exception as e:
        logger.error(f"Error generating metas status chart: {str(e)}")
        return func.HttpResponse(
            json.dumps({"error": "Failed to generate chart", "details": str(e)}),
            status_code=500,
            mimetype="application/json"
        )


def chart_sensor_data(req: func.HttpRequest) -> func.HttpResponse:
    """
    GET /api/visualization/sensor-data
    Generate charts for sensor data visualization
    Supports query parameters: days (number of days to visualize)
    """
    try:
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
            return func.HttpResponse(
                json.dumps({
                    "message": "No sensor data available",
                    "sample_structure": {
                        "timestamp": "ISO format datetime",
                        "temperature": "float",
                        "humidity": "float",
                        "soil_moisture": "float",
                        "light_intensity": "float"
                    }
                }),
                status_code=200,
                mimetype="application/json",
                headers={"Access-Control-Allow-Origin": "*"}
            )
        
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
        chart_base64 = generate_chart_base64(fig)
        
        return func.HttpResponse(
            json.dumps({
                "chart": f"data:image/png;base64,{chart_base64}",
                "statistics": charts_data,
                "data_points": len(df)
            }, ensure_ascii=False),
            status_code=200,
            mimetype="application/json",
            headers={"Access-Control-Allow-Origin": "*"}
        )
    except Exception as e:
        logger.error(f"Error generating sensor data chart: {str(e)}")
        return func.HttpResponse(
            json.dumps({"error": "Failed to generate chart", "details": str(e)}),
            status_code=500,
            mimetype="application/json"
        )


def main(req: func.HttpRequest) -> func.HttpResponse:
    """
    Main router for visualization endpoints
    """
    route = req.route_params.get('chart_type', '')
    
    if route == 'metas-status':
        return chart_metas_status(req)
    elif route == 'sensor-data':
        return chart_sensor_data(req)
    else:
        return func.HttpResponse(
            json.dumps({
                "error": "Invalid chart type",
                "available_charts": ["metas-status", "sensor-data"]
            }),
            status_code=400,
            mimetype="application/json"
        )
