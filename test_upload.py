import httpx
import json

url = "http://localhost:8000/api/parse-upload"
files = {'file': ('test.sarif', open('test.sarif', 'rb'), 'application/json')}

try:
    with httpx.Client() as client:
        response = client.post(url, files=files, timeout=30.0)
        response.raise_for_status()
        result = response.json()
        print(json.dumps(result, indent=2))
except Exception as e:
    print(f"Error: {e}")
