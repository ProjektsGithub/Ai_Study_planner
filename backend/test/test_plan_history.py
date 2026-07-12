"""
Test script for Task 13: Study Plan History and Versioning

Tests:
1. GET /api/v1/study-plans/history - Paginated history retrieval
2. POST /api/v1/study-plans/{id}/restore - Plan restoration
3. 90-day retention policy (delete_old_plans method)
"""
import requests
import json
from datetime import date, timedelta

BASE_URL = "http://localhost:8000/api/v1"

def print_section(title):
    """Print a section header"""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}\n")

def print_response(response):
    """Print response details"""
    print(f"Status: {response.status_code}")
    try:
        print(f"Response: {json.dumps(response.json(), indent=2)}")
    except:
        print(f"Response: {response.text}")

def register_and_login():
    """Register a test user and login"""
    print_section("SETUP: Register and Login")
    
    # Generate unique email
    import random
    import string
    unique_id = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
    email = f"test_history_{unique_id}@example.com"
    password = "TestPassword123!"
    
    print(f"Using test email: {email}")
    
    # Register
    register_data = {
        "email": email,
        "password": password,
        "name": "Test User History"
    }
    
    response = requests.post(f"{BASE_URL}/auth/register", json=register_data)
    if response.status_code == 201:
        print("✓ User registered successfully")
    else:
        print("✗ Registration failed")
        print_response(response)
        return None
    
    # Login
    login_data = {
        "email": email,
        "password": password
    }
    
    response = requests.post(f"{BASE_URL}/auth/login", json=login_data)
    if response.status_code == 200:
        token = response.json()["access_token"]
        print("✓ Login successful")
        return token
    else:
        print("✗ Login failed")
        print_response(response)
        return None

def create_test_data(token):
    """Create profile, subjects, and availabilities"""
    print_section("SETUP: Create Test Data")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Create profile
    profile_data = {
        "cursus": "Computer Science",
        "academic_level": "Bachelor",
        "weekly_study_goal": 20,
        "preferences": {"preferred_session_duration": 90}
    }
    
    response = requests.post(f"{BASE_URL}/profile", json=profile_data, headers=headers)
    if response.status_code in [200, 201]:
        print("✓ Profile created")
    else:
        print("ℹ Profile may already exist")
    
    # Create subjects
    subjects = [
        {
            "name": "Mathematics",
            "priority": 5,
            "difficulty": 4,
            "target_weekly_hours": 8,
            "exam_date": (date.today() + timedelta(days=30)).isoformat()
        },
        {
            "name": "Physics",
            "priority": 4,
            "difficulty": 5,
            "target_weekly_hours": 6,
            "exam_date": (date.today() + timedelta(days=45)).isoformat()
        }
    ]
    
    subject_ids = []
    for subject in subjects:
        response = requests.post(f"{BASE_URL}/subjects", json=subject, headers=headers)
        if response.status_code == 201:
            subject_ids.append(response.json()["id"])
            print(f"✓ Subject '{subject['name']}' created")
    
    # Create availabilities
    availabilities = [
        {"day_of_week": "Monday", "start_time": "09:00:00", "end_time": "12:00:00"},
        {"day_of_week": "Monday", "start_time": "14:00:00", "end_time": "17:00:00"},
        {"day_of_week": "Tuesday", "start_time": "09:00:00", "end_time": "12:00:00"},
        {"day_of_week": "Wednesday", "start_time": "09:00:00", "end_time": "12:00:00"},
        {"day_of_week": "Thursday", "start_time": "09:00:00", "end_time": "12:00:00"},
        {"day_of_week": "Friday", "start_time": "09:00:00", "end_time": "12:00:00"}
    ]
    
    for avail in availabilities:
        response = requests.post(f"{BASE_URL}/availabilities", json=avail, headers=headers)
        if response.status_code == 201:
            print(f"✓ Availability for {avail['day_of_week']} created")
    
    return subject_ids

def create_multiple_plans(token):
    """Create multiple study plans for different weeks"""
    print_section("TEST 1: Create Multiple Plans")
    
    headers = {"Authorization": f"Bearer {token}"}
    plan_ids = []
    
    # Create plans for 3 different weeks
    for i in range(3):
        week_start = date.today() + timedelta(weeks=i)
        # Ensure it's a Monday
        while week_start.weekday() != 0:
            week_start += timedelta(days=1)
        
        generate_data = {
            "week_start": week_start.isoformat(),
            "force_regenerate": True
        }
        
        print(f"\nGenerating plan for week starting {week_start}...")
        response = requests.post(f"{BASE_URL}/study-plans/generate", json=generate_data, headers=headers)
        
        if response.status_code == 200:
            result = response.json()
            if result.get("success"):
                plan_id = result.get("plan_id")
                plan_ids.append(plan_id)
                print(f"✓ Plan created: {plan_id}")
            else:
                print(f"✗ Plan generation failed: {result.get('message')}")
        else:
            print(f"✗ Request failed")
            print_response(response)
    
    return plan_ids

def test_plan_history(token):
    """Test GET /api/v1/study-plans/history endpoint"""
    print_section("TEST 2: Get Plan History (Pagination)")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Test page 1
    print("Fetching page 1...")
    response = requests.get(f"{BASE_URL}/study-plans/history?page=1", headers=headers)
    print_response(response)
    
    if response.status_code == 200:
        data = response.json()
        print(f"\n✓ History retrieved successfully")
        print(f"  Total plans: {data['total_count']}")
        print(f"  Page: {data['page']}/{data['total_pages']}")
        print(f"  Plans on this page: {len(data['plans'])}")
        
        # Display plan summaries
        for plan in data['plans']:
            print(f"\n  Plan: {plan['plan_id']}")
            print(f"    Week: {plan['week_start']}")
            print(f"    Status: {plan['status']}")
            print(f"    Sessions: {plan['session_count']}")
            print(f"    Total hours: {plan['total_hours']}")
            print(f"    Created: {plan['created_at']}")
        
        return data['plans']
    else:
        print("✗ Failed to retrieve history")
        return []

def test_plan_restoration(token, plan_ids):
    """Test POST /api/v1/study-plans/{id}/restore endpoint"""
    print_section("TEST 3: Restore Previous Plan")
    
    if not plan_ids:
        print("✗ No plans available to restore")
        return
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Get the first plan to restore
    plan_to_restore = plan_ids[0]
    
    print(f"Restoring plan: {plan_to_restore}...")
    response = requests.post(f"{BASE_URL}/study-plans/{plan_to_restore}/restore", headers=headers)
    print_response(response)
    
    if response.status_code == 200:
        result = response.json()
        if result.get("success"):
            print(f"\n✓ Plan restored successfully")
            print(f"  New plan ID: {result.get('plan_id')}")
            print(f"  Message: {result.get('message')}")
            
            # Verify the restored plan
            new_plan_id = result.get('plan_id')
            print(f"\nVerifying restored plan...")
            response = requests.get(f"{BASE_URL}/study-plans/{new_plan_id}", headers=headers)
            
            if response.status_code == 200:
                plan = response.json()
                print(f"✓ Restored plan verified")
                print(f"  Status: {plan['status']}")
                print(f"  Sessions: {len(plan['sessions'])}")
                print(f"  Total hours: {plan['total_hours']}")
            else:
                print("✗ Failed to verify restored plan")
        else:
            print("✗ Restoration failed")
    else:
        print("✗ Restoration request failed")

def test_pagination(token):
    """Test pagination with multiple pages"""
    print_section("TEST 4: Pagination (Multiple Pages)")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Test page 1
    print("Fetching page 1...")
    response = requests.get(f"{BASE_URL}/study-plans/history?page=1", headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        print(f"✓ Page 1: {len(data['plans'])} plans")
        print(f"  Total pages: {data['total_pages']}")
        
        # Test page 2 if it exists
        if data['total_pages'] > 1:
            print("\nFetching page 2...")
            response = requests.get(f"{BASE_URL}/study-plans/history?page=2", headers=headers)
            
            if response.status_code == 200:
                data2 = response.json()
                print(f"✓ Page 2: {len(data2['plans'])} plans")
            else:
                print("✗ Failed to fetch page 2")
        else:
            print("ℹ Only 1 page available (need more plans to test pagination)")
    else:
        print("✗ Failed to fetch page 1")

def test_invalid_restore(token):
    """Test restoring a non-existent plan"""
    print_section("TEST 5: Invalid Plan Restoration")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    fake_plan_id = "00000000-0000-0000-0000-000000000000"
    
    print(f"Attempting to restore non-existent plan: {fake_plan_id}...")
    response = requests.post(f"{BASE_URL}/study-plans/{fake_plan_id}/restore", headers=headers)
    print_response(response)
    
    if response.status_code == 404:
        print("✓ Correctly returned 404 for non-existent plan")
    else:
        print("✗ Expected 404 status code")

def test_retention_policy():
    """Test the 90-day retention policy (manual test)"""
    print_section("TEST 6: 90-Day Retention Policy")
    
    print("Note: This test requires manual execution of the delete_old_plans() method")
    print("The method can be called from a background job or admin endpoint.")
    print("\nExample usage:")
    print("  from app.services.study_plan_service import StudyPlanService")
    print("  from app.core.database import SessionLocal")
    print("  ")
    print("  db = SessionLocal()")
    print("  service = StudyPlanService(db)")
    print("  result = service.delete_old_plans(retention_days=90)")
    print("  print(result)")
    print("  db.close()")

def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("  TASK 13: STUDY PLAN HISTORY AND VERSIONING TESTS")
    print("="*60)
    
    # Setup
    token = register_and_login()
    if not token:
        print("\n✗ Failed to authenticate. Exiting.")
        return
    
    create_test_data(token)
    
    # Create multiple plans
    plan_ids = create_multiple_plans(token)
    
    # Test history retrieval
    history_plans = test_plan_history(token)
    
    # Extract plan IDs from history
    if history_plans:
        plan_ids_from_history = [p['plan_id'] for p in history_plans]
    else:
        plan_ids_from_history = plan_ids
    
    # Test plan restoration
    test_plan_restoration(token, plan_ids_from_history)
    
    # Test pagination
    test_pagination(token)
    
    # Test invalid restoration
    test_invalid_restore(token)
    
    # Test retention policy (informational)
    test_retention_policy()
    
    print("\n" + "="*60)
    print("  ALL TESTS COMPLETED")
    print("="*60 + "\n")

if __name__ == "__main__":
    main()
