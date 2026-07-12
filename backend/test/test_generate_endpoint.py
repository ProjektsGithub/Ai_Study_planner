"""
Test the study plan generation endpoint
"""
import requests
import json
from datetime import date, timedelta

BASE_URL = "http://localhost:8000"

# Get token for user 12 (the one we created)
def get_token():
    """Login and get token"""
    response = requests.post(
        f"{BASE_URL}/api/v1/auth/login",
        json={"email": "test@example.com", "password": "TestPassword123"}
    )
    if response.status_code == 200:
        return response.json()['access_token']
    return None

def test_generate_plan():
    """Test plan generation"""
    
    # Get token
    token = get_token()
    if not token:
        print("✗ Failed to get token")
        return
    
    print(f"✓ Got token: {token[:50]}...")
    
    # Get Monday of current week
    today = date.today()
    days_to_monday = (today.weekday()) % 7
    if days_to_monday == 0:
        monday = today
    else:
        monday = today - timedelta(days=days_to_monday)
    
    print(f"Week start (Monday): {monday}")
    
    # Test the endpoint
    headers = {"Authorization": f"Bearer {token}"}
    data = {
        "week_start": str(monday),
        "force_regenerate": False
    }
    
    print(f"\nTesting POST /api/v1/study-plans/generate")
    print(f"Data: {json.dumps(data, indent=2)}")
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/v1/study-plans/generate",
            json=data,
            headers=headers,
            timeout=30
        )
        
        print(f"\nStatus: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        
        if response.status_code == 200:
            print("\n✓ Plan generated successfully!")
        else:
            print(f"\n✗ Failed with status {response.status_code}")
            
    except Exception as e:
        print(f"\n✗ Error: {e}")

if __name__ == "__main__":
    test_generate_plan()
