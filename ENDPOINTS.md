# API Endpoints Reference

## 🔐 Authentication Endpoints

### POST /api/auth/register
Register a new user account.

**Request:**
```bash
curl -X POST http://localhost:7071/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "securepassword123",
    "name": "User Name"
  }'
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

---

### POST /api/auth/login
Authenticate and receive JWT token.

**Request:**
```bash
curl -X POST http://localhost:7071/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "securepassword123"
  }'
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

---

### GET /api/auth/verify
Verify JWT token validity.

**Request:**
```bash
curl http://localhost:7071/api/auth/verify \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
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

---

## 📊 Health Check

### GET /api/health
Check API and database status.

**Request:**
```bash
curl http://localhost:7071/api/health
```

---

## 📝 Metas Endpoints

> **Note:** All metas endpoints require authentication. Create/Update/Delete require admin role.

### GET /api/metas
Get all metas (requires auth token).

**Request:**
```bash
curl http://localhost:7071/api/metas \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

### GET /api/metas/{id}
Get a specific meta by ID (requires auth token).

### POST /api/metas
Create a new meta (requires admin token).

**Request:**
```bash
curl -X POST http://localhost:7071/api/metas \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ADMIN_TOKEN_HERE" \
  -d '{
    "titulo": "Nova Meta",
    "descricao": "Descrição da meta",
    "status": "pendente"
  }'
```

### PUT /api/metas/{id}
Update a meta (requires admin token).

### DELETE /api/metas/{id}
Delete a meta (requires admin token).

---

## 📈 Visualization Endpoints

### GET /api/visualization/metas-status
Get pie chart of metas by status.

### GET /api/visualization/sensor-data?days=7
Get sensor data charts.

---

## 🚀 Quick Start

1. **Start the API:**
   ```bash
   cd api
   func start
   ```

2. **Register a user:**
   ```bash
   curl -X POST http://localhost:7071/api/auth/register \
     -H "Content-Type: application/json" \
     -d '{"email":"admin@example.com","password":"admin123","name":"Admin User"}'
   ```

3. **Login:**
   ```bash
   curl -X POST http://localhost:7071/api/auth/login \
     -H "Content-Type: application/json" \
     -d '{"email":"admin@example.com","password":"admin123"}'
   ```

4. **Use the token** in subsequent requests with `Authorization: Bearer <token>` header.
