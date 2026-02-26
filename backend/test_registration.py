import requests
import json

URL = "https://eclproj.onrender.com/api/auth/register"
# You can also test locally if running
# URL = "http://localhost:8000/api/auth/register"

def test_register():
    payload = {
        "email": "testuser@example.com",
        "password": "testpassword123",
        "full_name": "Test User"
    }
    
    print(f"Testing registration with payload: {payload}")
    response = requests.post(URL, json=payload)
    
    print(f"Status Code: {response.status_code}")
    print(f"Response Body: {json.dumps(response.json(), indent=2)}")

if __name__ == "__main__":
    try:
        test_register()
    except Exception as e:
        print(f"An error occurred: {e}")
