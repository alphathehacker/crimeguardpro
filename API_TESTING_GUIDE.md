# API Testing Guide - Postman

## Quick Start

1. **Start the Flask server:**
   ```bash
   python app.py
   ```
   You should see: `Running on http://127.0.0.1:5000`

2. **Base URL:** `http://localhost:5000` or `http://127.0.0.1:5000`

## Available Routes (Test these in Postman)

### ✅ Check if server is running
- **URL:** `http://localhost:5000/`
- **Method:** GET
- **Expected:** `{"message": "✅ Flask Crime Management System is running!"}`

### ✅ List all available routes
- **URL:** `http://localhost:5000/api/routes`
- **Method:** GET
- **Expected:** JSON with all available routes

---

## Authentication Routes

### Register Citizen
- **URL:** `http://localhost:5000/api/register/citizen`
- **Method:** POST
- **Headers:** 
  - `Content-Type: application/json`
- **Body (JSON):**
  ```json
  {
    "first_name": "John",
    "last_name": "Doe",
    "email": "john@example.com",
    "phone": "1234567890",
    "password": "password123"
  }
  ```

### Register Officer
- **URL:** `http://localhost:5000/api/register/officer`
- **Method:** POST
- **Headers:** 
  - `Content-Type: application/json`
- **Body (JSON):**
  ```json
  {
    "first_name": "Jane",
    "last_name": "Smith",
    "email": "jane@example.com",
    "department": "Police",
    "badge_number": "12345",
    "supervisor_name": "Supervisor Name",
    "password": "password123"
  }
  ```

### Register Admin
- **URL:** `http://localhost:5000/api/register/admin`
- **Method:** POST
- **Headers:** 
  - `Content-Type: application/json`
- **Body (JSON):**
  ```json
  {
    "full_name": "Admin User",
    "employee_id": "EMP001",
    "department": "IT",
    "email": "admin@example.com",
    "reason_for_access": "System Administrator",
    "password": "password123"
  }
  ```

### Login
- **URL:** `http://localhost:5000/api/login`
- **Method:** POST
- **Headers:** 
  - `Content-Type: application/json`
- **Body (JSON):**
  ```json
  {
    "email": "john@example.com",
    "password": "password123"
  }
  ```
- **Important:** After login, Postman will automatically save the session cookie. Use this for authenticated routes.

---

## Case Management Routes

### Get All Cases
- **URL:** `http://localhost:5000/api/cases`
- **Method:** GET
- **Headers:** None required (but session cookie needed if logged in)

### Create Case
- **URL:** `http://localhost:5000/api/cases`
- **Method:** POST
- **Headers:** 
  - `Content-Type: application/json`
- **Body (JSON):**
  ```json
  {
    "title": "Case Title",
    "description": "Case Description"
  }
  ```
- **Note:** Requires login (session cookie from `/api/login`)

---

## Dashboard Routes

### Get Dashboard Data
- **URL:** `http://localhost:5000/api/dashboard_data`
- **Method:** GET

---

## Profile Routes

### Citizen Profile
- **URL:** `http://localhost:5000/api/citizen/profile`
- **Method:** GET

### Officer Profile
- **URL:** `http://localhost:5000/api/officer/profile`
- **Method:** GET

### Admin Profile
- **URL:** `http://localhost:5000/api/admin/profile`
- **Method:** GET

---

## Troubleshooting "Method Not Found" Error

### Common Issues:

1. **Wrong URL**
   - ✅ Correct: `http://localhost:5000/api/login`
   - ❌ Wrong: `http://localhost:5000/login` (missing `/api`)
   - ❌ Wrong: `http://localhost:5000/api/login/` (trailing slash)

2. **Wrong HTTP Method**
   - ✅ `/api/login` requires POST
   - ❌ Using GET will give "Method Not Allowed"

3. **Server Not Running**
   - Make sure Flask server is running
   - Check terminal for: `Running on http://127.0.0.1:5000`

4. **CORS Issues**
   - CORS is enabled, but make sure you're using the correct headers
   - Use `Content-Type: application/json` for POST requests

5. **Check Available Routes**
   - Visit `http://localhost:5000/api/routes` in browser or Postman
   - This will show all registered routes

### Testing Steps:

1. **Test Base Route:**
   ```
   GET http://localhost:5000/
   ```
   Should return success message

2. **List Routes:**
   ```
   GET http://localhost:5000/api/routes
   ```
   Should show all available routes

3. **Test Registration:**
   ```
   POST http://localhost:5000/api/register/citizen
   Content-Type: application/json
   ```
   With JSON body

4. **Test Login:**
   ```
   POST http://localhost:5000/api/login
   Content-Type: application/json
   ```
   With email and password

---

## Postman Setup Tips

1. **Create Environment Variables:**
   - `base_url` = `http://localhost:5000`

2. **Enable Cookie Management:**
   - Postman automatically saves cookies from login
   - Check "Cookies" tab in Postman

3. **Save Common Requests:**
   - Save registration, login, etc. as collections

4. **Check Response:**
   - If you get 404: Route doesn't exist (check URL)
   - If you get 405: Wrong HTTP method
   - If you get 400: Missing required fields in body

---

## Expected Responses

### Success Response:
```json
{
  "success": true,
  "message": "Citizen account created successfully"
}
```

### Error Response (404):
```json
{
  "error": "Route not found",
  "message": "The requested URL was not found on the server.",
  "hint": "Check the URL path and ensure you're using the correct HTTP method (GET, POST, etc.)",
  "available_routes": "/api/routes"
}
```

### Error Response (405):
```json
{
  "error": "Method not allowed",
  "message": "The HTTP method is not allowed for this route.",
  "hint": "Check if you're using the correct HTTP method (GET, POST, PUT, DELETE, etc.)",
  "available_routes": "/api/routes"
}
```

