# AÇAIMAR API - Azure Functions

API layer for the AÇAIMAR project built with Azure Functions (Python) and MongoDB.

## 🏗️ Architecture

- **Runtime**: Python 3.9+
- **Framework**: Azure Functions v2
- **Database**: MongoDB
- **Data Visualization**: Matplotlib, Seaborn, Pandas

## 📁 Project Structure

```
api/
├── shared/
│   └── db_connection.py      # MongoDB connection utility
├── get_metas/                # GET /api/metas
├── get_meta/                 # GET /api/metas/{id}
├── create_meta/              # POST /api/metas
├── update_meta/              # PUT /api/metas/{id}
├── delete_meta/              # DELETE /api/metas/{id}
├── visualization/            # Data visualization endpoints
├── host.json                 # Azure Functions host configuration
├── requirements.txt          # Python dependencies
└── local.settings.json       # Local environment variables (not in git)
```

## 🚀 Getting Started

### Prerequisites

- Python 3.9 or higher
- Azure Functions Core Tools v4
- MongoDB instance (local or cloud)
- Azure account (for deployment)

### Local Development Setup

1. **Install Azure Functions Core Tools**

   ```bash
   # On Linux/WSL
   curl https://packages.microsoft.com/keys/microsoft.asc | gpg --dearmor > microsoft.gpg
   sudo mv microsoft.gpg /etc/apt/trusted.gpg.d/microsoft.gpg
   sudo sh -c 'echo "deb [arch=amd64,arm64,armhf] https://packages.microsoft.com/repos/microsoft-ubuntu-$(lsb_release -cs)-prod $(lsb_release -cs) main" > /etc/apt/sources.list.d/dotnetdev.list'
   sudo apt-get update
   sudo apt-get install azure-functions-core-tools-4
   ```

2. **Create virtual environment**

   ```bash
   cd api
   python3 -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**

   Copy the example settings file and configure your MongoDB connection:

   ```bash
   cp local.settings.json.example local.settings.json
   ```

   Edit `local.settings.json` with your MongoDB connection string:

   ```json
   {
     "IsEncrypted": false,
     "Values": {
       "AzureWebJobsStorage": "UseDevelopmentStorage=true",
       "FUNCTIONS_WORKER_RUNTIME": "python",
       "MONGODB_CONNECTION_STRING": "mongodb://your-connection-string",
       "MONGODB_DATABASE": "acaimar",
       "AZURE_FUNCTIONS_ENVIRONMENT": "Development"
     }
   }
   ```

5. **Run locally**

   ```bash
   func start
   ```

   The API will be available at `http://localhost:7071/api/`

## 📡 API Endpoints

### Authentication Endpoints

#### POST /api/auth/register
Register a new user.

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "securepassword",
  "name": "User Name"
}
```

**Response:**
```json
{
  "_id": "507f1f77bcf86cd799439011",
  "email": "user@example.com",
  "name": "User Name",
  "role": "user",
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

#### POST /api/auth/login
Authenticate user and receive JWT token.

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "securepassword"
}
```

**Response:**
```json
{
  "_id": "507f1f77bcf86cd799439011",
  "email": "user@example.com",
  "name": "User Name",
  "role": "user",
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

#### GET /api/auth/verify
Verify JWT token validity.

**Headers:**
```
Authorization: Bearer <token>
```

**Response:**
```json
{
  "user_id": "507f1f77bcf86cd799439011",
  "email": "user@example.com",
  "role": "user",
  "valid": true
}
```

### Metas (Goals) Endpoints

> **Note**: All metas endpoints require authentication. Create/Update/Delete require admin role.

#### GET /api/metas
Retrieve all metas.

**Response:**
```json
[
  {
    "_id": "507f1f77bcf86cd799439011",
    "titulo": "Implementação de Rede de Sensores IoT",
    "descricao": "...",
    "status": "em-andamento"
  }
]
```

#### GET /api/metas/{id}
Retrieve a specific meta by ID.

#### POST /api/metas
Create a new meta.

**Request Body:**
```json
{
  "titulo": "Nova Meta",
  "descricao": "Descrição da meta",
  "status": "pendente"
}
```

#### PUT /api/metas/{id}
Update an existing meta.

#### DELETE /api/metas/{id}
Delete a meta.

### Health Check Endpoint

#### GET /api/health
Check API and database health status.

**Response (Healthy):**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:00.000000",
  "service": "AÇAIMAR API",
  "version": "1.0.0",
  "checks": {
    "api": {
      "status": "ok",
      "message": "API is running"
    },
    "database": {
      "status": "ok",
      "message": "Database connection successful",
      "database": "acaimar",
      "collections": 2,
      "dataSize": 1024
    }
  }
}
```

**Response (Degraded - Database Error):**
```json
{
  "status": "degraded",
  "timestamp": "2024-01-15T10:30:00.000000",
  "service": "AÇAIMAR API",
  "version": "1.0.0",
  "checks": {
    "api": {
      "status": "ok",
      "message": "API is running"
    },
    "database": {
      "status": "error",
      "message": "Database connection failed: ..."
    }
  }
}
```

**Status Codes:**
- `200 OK` - All systems healthy
- `503 Service Unavailable` - Database connection failed

### Visualization Endpoints

#### GET /api/visualization/metas-status
Generate a pie chart showing the distribution of metas by status.

**Response:**
```json
{
  "chart": "data:image/png;base64,...",
  "data": {
    "em-andamento": 3,
    "pendente": 2,
    "concluido": 1
  }
}
```

#### GET /api/visualization/sensor-data?days=7
Generate time series charts for sensor data.

**Query Parameters:**
- `days` (optional): Number of days to visualize (default: 7)

**Response:**
```json
{
  "chart": "data:image/png;base64,...",
  "statistics": {
    "temperature": {
      "mean": 25.5,
      "min": 20.0,
      "max": 30.0,
      "std": 2.5
    }
  },
  "data_points": 168
}
```

## 🗄️ Database Schema

### Metas Collection
```json
{
  "_id": "ObjectId",
  "titulo": "string",
  "descricao": "string",
  "status": "pendente | em-andamento | concluido"
}
```

### Sensor Data Collection (for visualization)
```json
{
  "_id": "ObjectId",
  "timestamp": "ISO datetime string",
  "temperature": "float",
  "humidity": "float",
  "soil_moisture": "float",
  "light_intensity": "float"
}
```

## 🚢 Deployment to Azure

1. **Create Azure Function App**

   ```bash
   az functionapp create \
     --resource-group <resource-group> \
     --consumption-plan-location <location> \
     --runtime python \
     --runtime-version 3.9 \
     --functions-version 4 \
     --name <function-app-name> \
     --storage-account <storage-account-name>
   ```

2. **Configure Application Settings**

   ```bash
   az functionapp config appsettings set \
     --name <function-app-name> \
     --resource-group <resource-group> \
     --settings \
       MONGODB_CONNECTION_STRING="<your-connection-string>" \
       MONGODB_DATABASE="acaimar"
   ```

3. **Deploy**

   ```bash
   func azure functionapp publish <function-app-name>
   ```

## 🧪 Testing

You can test the API using curl or any HTTP client:

```bash
# Health check
curl http://localhost:7071/api/health

# Get all metas (requires auth token)
curl http://localhost:7071/api/metas \
  -H "Authorization: Bearer <your-token>"

# Create a meta (requires admin token)
curl -X POST http://localhost:7071/api/metas \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <admin-token>" \
  -d '{"titulo": "Test Meta", "descricao": "Test Description", "status": "pendente"}'

# Get visualization
curl http://localhost:7071/api/visualization/metas-status
```

## 📦 Dependencies

- `azure-functions` - Azure Functions runtime
- `pymongo` - MongoDB driver
- `pandas` - Data manipulation
- `matplotlib` - Chart generation
- `seaborn` - Enhanced visualizations
- `numpy` - Numerical operations

## 🔒 Security Notes

- In production, set `authLevel` to `function` or `admin` in `function.json`
- Store MongoDB connection strings in Azure Key Vault or App Settings
- Enable CORS properly for your frontend domain
- Use environment-specific connection strings

## 📝 Notes

- The visualization functions return base64-encoded PNG images
- All endpoints include CORS headers for development
- ObjectId fields are automatically converted to strings in responses
- Error responses include detailed error messages in development mode
