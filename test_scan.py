import httpx
import json

url = "http://localhost:8000/api/github/scan"
data = {
    "email": "dev@example.com",
    "repo_url": "https://github.com/expressjs/express",
    "deep_scan": True
}

try:
    with httpx.Client() as client:
        response = client.post(url, json=data, timeout=60.0)
        response.raise_for_status()
        result = response.json()
        print(f"Scan successful for: {result['scan']['full_name']}")
        print(f"Analysis Title: {result['analysis']['title']}")
except Exception as e:
    print(f"Error: {e}")
