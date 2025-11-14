# How to Fix "Method Not Found" Error

## The Problem
The route `/api/routes` exists and is registered correctly, but you're getting "method not found" error.

## Solution: Restart the Flask Server

### Step 1: Stop the current server (if running)
- Press `Ctrl+C` in the terminal where Flask is running
- Or close the terminal window

### Step 2: Start the server fresh
```bash
python app.py
```

You should see:
```
Using database: sqlite:///crime_management.db
 * Running on http://127.0.0.1:5000
 * Debug mode: on
```

### Step 3: Test the route
Open your browser or Postman and go to:
```
http://127.0.0.1:5000/api/routes
```

Or test in PowerShell:
```powershell
Invoke-RestMethod -Uri http://127.0.0.1:5000/api/routes -Method GET
```

## Verify Route is Registered

Before starting the server, you can verify the route exists:
```bash
python test_server.py
```

This will show you all registered routes.

## Common Issues

### Issue 1: Server not running
- **Symptom**: Connection refused error
- **Solution**: Start the server with `python app.py`

### Issue 2: Server running old code
- **Symptom**: Route not found even though code exists
- **Solution**: Restart the server (Ctrl+C, then `python app.py`)

### Issue 3: Port already in use
- **Symptom**: "Address already in use" error
- **Solution**: 
  - Find and kill the process using port 5000
  - Or change port in `app.py` (last line): `app.run(debug=True, port=5001)`

### Issue 4: Wrong URL in Postman
- Make sure you're using: `http://127.0.0.1:5000/api/routes`
- NOT: `http://localhost:5000/api/routes/` (trailing slash)
- NOT: `http://127.0.0.1:5000/routes` (missing `/api`)

## Expected Response

When you access `http://127.0.0.1:5000/api/routes`, you should get:
```json
{
  "message": "Available API routes",
  "total_routes": 16,
  "routes": [
    {
      "path": "/",
      "methods": ["GET"],
      "endpoint": "home"
    },
    {
      "path": "/api/login",
      "methods": ["POST"],
      "endpoint": "auth.login_user"
    },
    ... (and more routes)
  ]
}
```

If you get this, the server is working correctly!

