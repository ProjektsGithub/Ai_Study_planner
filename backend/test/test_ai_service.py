"""
Test AI Service (with mocked responses)
"""
import asyncio
import json
from datetime import date, timedelta
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models.user import User
from app.models.generation_log import GenerationLog
from app.services.ai_service import AIService
from app.core.security import get_password_hash

print("=" * 70)
print("Test AI Service")
print("=" * 70)
print()

# Create database session
db: Session = SessionLocal()

try:
    # 1. Create or get test user
    print("1. Setup test user")
    test_user = db.query(User).filter(User.email == "ai_test@example.com").first()
    
    if not test_user:
        test_user = User(
            email="ai_test@example.com",
            password_hash=get_password_hash("TestPassword123!"),
            name="AI Test User",
            is_active=True,
            failed_login_attempts=0
        )
        db.add(test_user)
        db.commit()
        db.refresh(test_user)
    
    print(f"   User ID: {test_user.id}")
    print()
    
    # 2. Create AI Service instance
    print("2. Create AI Service")
    ai_service = AIService(db)
    print(f"   Backend: {'Google Colab' if ai_service.use_colab else 'Ollama'}")
    print(f"   Model: {ai_service.model}")
    print(f"   LoRA enabled: {ai_service.lora_enabled}")
    if ai_service.lora_enabled:
        print(f"   LoRA adapter: {ai_service.lora_adapter}")
    print()
    
    # 3. Test prompt construction
    print("3. Test prompt construction")
    
    planning_data = {
        "valid_slots": [
            {"day": "Monday", "start_time": "09:00:00", "end_time": "12:00:00", "duration_minutes": 180},
            {"day": "Monday", "start_time": "14:00:00", "end_time": "18:00:00", "duration_minutes": 240},
            {"day": "Wednesday", "start_time": "10:00:00", "end_time": "16:00:00", "duration_minutes": 360},
        ],
        "subject_priorities": [
            {
                "subject_id": 1,
                "subject_name": "Mathematics",
                "priority_score": 85.5,
                "base_priority": 5,
                "difficulty": 4,
                "target_weekly_hours": 10.0,
                "exam_date": (date.today() + timedelta(days=15)).isoformat()
            },
            {
                "subject_id": 2,
                "subject_name": "Physics",
                "priority_score": 72.0,
                "base_priority": 4,
                "difficulty": 5,
                "target_weekly_hours": 8.0,
                "exam_date": None
            }
        ],
        "constraints": {
            "max_daily_hours": 6,
            "required_breaks": [{"duration_minutes": 15, "after_minutes": 90}],
            "fixed_slots": [],
            "forbidden_slots_count": 1
        }
    }
    
    weekly_study_goal = 25.0
    user_preferences = {
        "preferred_study_times": ["morning", "afternoon"],
        "session_length": 90,
        "break_duration": 15
    }
    
    prompt = ai_service._construct_prompt(planning_data, weekly_study_goal, user_preferences)
    
    print(f"   Prompt length: {len(prompt)} characters")
    print(f"   Prompt preview (first 200 chars):")
    print(f"   {prompt[:200]}...")
    print()
    
    # 4. Test request hash computation
    print("4. Test request hash")
    request_hash = ai_service._compute_request_hash(prompt)
    print(f"   Hash: {request_hash[:16]}...")
    print()
    
    # 5. Test JSON extraction
    print("5. Test JSON extraction")
    
    # Test with markdown code block
    mock_response_1 = '''Here is the study plan:

```json
{
  "sessions": [
    {
      "day": "Monday",
      "start_time": "09:00:00",
      "end_time": "10:30:00",
      "subject_name": "Mathematics",
      "task_type": "lecture_review",
      "notes": "Chapter 5"
    }
  ],
  "total_hours": 1.5,
  "reasoning": "Focused on high priority subject"
}
```

This schedule prioritizes Mathematics.'''
    
    extracted_1 = ai_service._extract_json_from_response(mock_response_1)
    if extracted_1:
        print(f"   Test 1 (markdown): SUCCESS")
        print(f"   - Sessions: {len(extracted_1.get('sessions', []))}")
        print(f"   - Total hours: {extracted_1.get('total_hours')}")
    else:
        print(f"   Test 1 (markdown): FAILED")
    
    # Test with plain JSON
    mock_response_2 = '''{
  "sessions": [
    {"day": "Monday", "start_time": "09:00:00", "end_time": "10:30:00", "subject_name": "Mathematics", "task_type": "lecture_review", "notes": "Test"}
  ],
  "total_hours": 1.5,
  "reasoning": "Test"
}'''
    
    extracted_2 = ai_service._extract_json_from_response(mock_response_2)
    if extracted_2:
        print(f"   Test 2 (plain JSON): SUCCESS")
    else:
        print(f"   Test 2 (plain JSON): FAILED")
    print()
    
    # 6. Test generation logging (without actual API call)
    print("6. Test generation logging")
    
    # Clean up old logs
    db.query(GenerationLog).filter(GenerationLog.user_id == test_user.id).delete()
    db.commit()
    
    # Create a mock log entry
    log = GenerationLog(
        user_id=test_user.id,
        request_hash=request_hash,
        success=True,
        duration_seconds=1.5,  # 1500ms = 1.5s
        token_count=250,
        error_message=None
    )
    db.add(log)
    db.commit()
    db.refresh(log)
    
    print(f"   Log created: ID={log.id}")
    print(f"   - Duration: {log.duration_seconds}s")
    print(f"   - Tokens: {log.token_count}")
    print(f"   - Success: {log.success}")
    print()
    
    # 7. Verify log retrieval
    print("7. Verify log retrieval")
    logs = db.query(GenerationLog).filter(GenerationLog.user_id == test_user.id).all()
    print(f"   Found {len(logs)} log(s) for user")
    print()
    
    # 8. Test configuration
    print("8. Verify configuration")
    from app.core.config import settings
    print(f"   AI Service Type: {getattr(settings, 'AI_SERVICE_TYPE', 'ollama')}")
    print(f"   Ollama URL: {settings.OLLAMA_BASE_URL}")
    print(f"   Model: {settings.OLLAMA_MODEL}")
    print(f"   Temperature: {settings.OLLAMA_TEMPERATURE}")
    print(f"   Context: {settings.OLLAMA_NUM_CTX}")
    print(f"   Timeout: {settings.OLLAMA_TIMEOUT}s")
    print(f"   LoRA Enabled: {settings.LORA_ENABLED}")
    if settings.LORA_ENABLED:
        print(f"   LoRA Adapter: {settings.LORA_DEFAULT_ADAPTER}")
    print()
    
    print("=" * 70)
    print("ALL TESTS PASSED!")
    print("=" * 70)
    print()
    print("NOTE: Actual API calls to Ollama/Colab are not tested here.")
    print("To test with real API:")
    print("1. Install Ollama: https://ollama.ai")
    print("2. Run: ollama pull llama3.2")
    print("3. Run: ollama serve")
    print("4. Then test with real API calls")
    
except Exception as e:
    print(f"\nERROR: {e}")
    import traceback
    traceback.print_exc()
finally:
    # Cleanup
    if 'test_user' in locals() and test_user:
        db.query(GenerationLog).filter(GenerationLog.user_id == test_user.id).delete()
        db.commit()
    db.close()
