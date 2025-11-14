"""Test script for officer login functionality"""
import requests
import json

BASE_URL = "http://127.0.0.1:5000"

print("=" * 60)
print("OFFICER LOGIN API TEST")
print("=" * 60)

# Test 1: Check if login endpoint exists
print("\n[TEST 1] Checking login endpoint...")
try:
    response = requests.options(f"{BASE_URL}/api/login")
    print(f"[OK] Login endpoint exists: /api/login")
except Exception as e:
    print(f"[ERROR] Could not reach server: {e}")
    exit(1)

# Test 2: Try login with missing fields
print("\n[TEST 2] Testing with missing email...")
response = requests.post(
    f"{BASE_URL}/api/login",
    json={"password": "test123"},
    headers={"Content-Type": "application/json"}
)
print(f"Status: {response.status_code}")
print(f"Response: {response.json()}")

# Test 3: Try login with invalid credentials
print("\n[TEST 3] Testing with invalid credentials...")
response = requests.post(
    f"{BASE_URL}/api/login",
    json={"email": "nonexistent@example.com", "password": "wrongpass"},
    headers={"Content-Type": "application/json"}
)
print(f"Status: {response.status_code}")
print(f"Response: {response.json()}")

# Test 4: Show what valid request should look like
print("\n[TEST 4] Valid request format:")
print("POST /api/login")
print("Headers: Content-Type: application/json")
print("Body: {")
print('  "email": "officer@example.com",')
print('  "password": "your_password"')
print("}")

print("\n" + "=" * 60)
print("To test with a real officer account:")
print("1. First register an officer via POST /api/register/officer")
print("2. Then use that email/password to login")
print("=" * 60)

