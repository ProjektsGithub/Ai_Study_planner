"""
Test the complete registration and login flow
"""
import requests
import json
import random
import string

BASE_URL = "http://localhost:8000"

def random_email():
    """Generate a random email"""
    random_str = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
    return f"test_{random_str}@example.com"

def test_full_flow():
    """Test registration, login, and accessing protected endpoint"""
    
    # Generate random user data
    email = random_email()
    password = "TestPassword123"
    name = "Test User"
    
    print("=" * 60)
    print("TESTING FULL REGISTRATION AND LOGIN FLOW")
    print("=" * 60)
    
    # Step 1: Register
    print(f"\n1. REGISTRATION")
    print(f"   Email: {email}")
    print(f"   Password: {password}")
    print(f"   Name: {name}")
    
    try:
        reg_response = requests.post(
            f"{BASE_URL}/api/v1/auth/register",
            json={"email": email, "password": password, "name": name},
            timeout=10
        )
        
        print(f"   Status: {reg_response.status_code}")
        
        if reg_response.status_code == 201:
            print(f"   ✓ Registration successful!")
            user_data = reg_response.json()
            print(f"   User ID: {user_data['id']}")
            print(f"   Email: {user_data['email']}")
            print(f"   Name: {user_data['name']}")
        else:
            print(f"   ✗ Registration failed: {reg_response.json()}")
            return False
            
    except Exception as e:
        print(f"   ✗ Registration error: {e}")
        return False
    
    # Step 2: Login
    print(f"\n2. LOGIN")
    print(f"   Email: {email}")
    print(f"   Password: {password}")
    
    try:
        login_response = requests.post(
            f"{BASE_URL}/api/v1/auth/login",
            json={"email": email, "password": password},
            timeout=10
        )
        
        print(f"   Status: {login_response.status_code}")
        
        if login_response.status_code == 200:
            print(f"   ✓ Login successful!")
            tokens = login_response.json()
            access_token = tokens['access_token']
            refresh_token = tokens['refresh_token']
            print(f"   Access Token: {access_token[:50]}...")
            print(f"   Refresh Token: {refresh_token[:50]}...")
        else:
            print(f"   ✗ Login failed: {login_response.json()}")
            return False
            
    except Exception as e:
        print(f"   ✗ Login error: {e}")
        return False
    
    # Step 3: Access protected endpoint
    print(f"\n3. ACCESS PROTECTED ENDPOINT (/auth/me)")
    
    try:
        headers = {"Authorization": f"Bearer {access_token}"}
        me_response = requests.get(
            f"{BASE_URL}/api/v1/auth/me",
            headers=headers,
            timeout=10
        )
        
        print(f"   Status: {me_response.status_code}")
        
        if me_response.status_code == 200:
            print(f"   ✓ Successfully accessed protected endpoint!")
            user_info = me_response.json()
            print(f"   User ID: {user_info['id']}")
            print(f"   Email: {user_info['email']}")
            print(f"   Name: {user_info['name']}")
        else:
            print(f"   ✗ Failed to access protected endpoint: {me_response.json()}")
            return False
            
    except Exception as e:
        print(f"   ✗ Protected endpoint error: {e}")
        return False
    
    # Step 4: Try to access other protected endpoints
    print(f"\n4. ACCESS OTHER PROTECTED ENDPOINTS")
    
    endpoints = [
        "/api/v1/subjects",
        "/api/v1/availabilities",
        "/api/v1/constraints",
        "/api/v1/study-plans/current"
    ]
    
    for endpoint in endpoints:
        try:
            response = requests.get(
                f"{BASE_URL}{endpoint}",
                headers=headers,
                timeout=10
            )
            print(f"   {endpoint}: {response.status_code}")
        except Exception as e:
            print(f"   {endpoint}: Error - {e}")
    
    print("\n" + "=" * 60)
    print("✓ ALL TESTS PASSED!")
    print("=" * 60)
    return True

if __name__ == "__main__":
    test_full_flow()
