import httpx
import json

url = "http://localhost:8000/api/plan-fix"
data = {
    "email": "dev@example.com",
    "alert_text": "Critical SQL Injection in login.php",
    "user_request": "Fix the vulnerability",
    "simulate_attack": True
}

try:
    with httpx.Client() as client:
        response = client.post(url, json=data, timeout=30.0)
        response.raise_for_status()
        result = response.json()
        print(json.dumps(result, indent=2))
except Exception as e:
    print(f"Error: {e}")
