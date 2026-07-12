"""
Test the login endpoint
"""
import requests
import json

BASE_URL = "http://localhost:8000"

def test_login():
    """Test user login"""
    
    # Test data (using the user we just created)
    login_data = {
        "email": "test@example.com",
        "password": "TestPassword123"
    }
    
    print("Testing login endpoint...")
    print(f"URL: {BASE_URL}/api/v1/auth/login")
    print(f"Data: {json.dumps(login_data, indent=2)}")
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/v1/auth/login",
            json=login_data,
            timeout=10
        )
        
        print(f"\nStatus Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Response: {json.dumps(data, indent=2)}")
            print("\n✓ Login successful!")
            print(f"Access Token: {data.get('access_token', 'N/A')[:50]}...")
            return True
        else:
            print(f"Response: {json.dumps(response.json(), indent=2)}")
            print(f"\n✗ Login failed with status {response.status_code}")
            return False
            
    except requests.exceptions.Timeout:
        print("\n✗ Request timed out!")
        return False
    except Exception as e:
        print(f"\n✗ Error: {e}")
        return False

if __name__ == "__main__":
    test_login()
