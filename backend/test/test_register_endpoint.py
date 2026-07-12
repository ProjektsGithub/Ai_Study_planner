"""
Test the registration endpoint
"""
import requests
import json

BASE_URL = "http://localhost:8000"

def test_registration():
    """Test user registration"""
    
    # Test data
    user_data = {
        "email": "test@example.com",
        "password": "TestPassword123",
        "name": "Test User"
    }
    
    print("Testing registration endpoint...")
    print(f"URL: {BASE_URL}/api/v1/auth/register")
    print(f"Data: {json.dumps(user_data, indent=2)}")
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/v1/auth/register",
            json=user_data,
            timeout=10
        )
        
        print(f"\nStatus Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        
        if response.status_code in [200, 201]:
            print("\n✓ Registration successful!")
            return True
        else:
            print(f"\n✗ Registration failed with status {response.status_code}")
            return False
            
    except requests.exceptions.Timeout:
        print("\n✗ Request timed out!")
        return False
    except Exception as e:
        print(f"\n✗ Error: {e}")
        return False

if __name__ == "__main__":
    test_registration()
