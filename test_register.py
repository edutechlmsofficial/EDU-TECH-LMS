import requests
import json

# Test registration phase 2 with testing mode
url = 'http://localhost:5000/api/register'
data = {
    "phase": 2,
    "username": "testuser",
    "email": "test@example.com",
    "password": "password123",
    "role": "teacher",
    "is_testing": True
}

response = requests.post(url, json=data)
print(f"Status Code: {response.status_code}")
print(f"Response: {response.json()}")
