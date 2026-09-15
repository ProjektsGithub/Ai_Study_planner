import sys
sys.path.insert(0, 'backend')
from app.services.ai_service import AIService
from unittest.mock import MagicMock

db = MagicMock()
ai = AIService(db)

# Test 1: Temperature is at least 0.35
assert ai.temperature >= 0.35, f"Expected temperature >= 0.35, got {ai.temperature}"
print(f"[OK] AI Service temperature: {ai.temperature}")

# Test 2: Prompt doesn't contain hardcoded static exercise example
sample_planning_data = {
    "valid_slots": [
        {"day": "Monday", "start_time": "09:00:00", "end_time": "12:00:00", "duration_minutes": 180},
        {"day": "Wednesday", "start_time": "14:00:00", "end_time": "18:00:00", "duration_minutes": 240},
    ],
    "subject_priorities": [
        {"subject_id": 1, "subject_name": "Mathematics", "priority_score": 85.0, "target_weekly_hours": 8.0, "exam_date": None}
    ],
    "constraints": {
        "max_daily_hours": 6,
        "required_breaks": [],
        "fixed_slots": [],
        "forbidden_slots_count": 0
    }
}
prompt = ai._construct_prompt(sample_planning_data, 15.0, {})
assert "Solve problems 5.1, 5.3" not in prompt, "Found old hardcoded example in prompt!"
assert "STRICT ANTI-REPETITION" in prompt, "Missing anti-repetition instruction in prompt"
print("[OK] Prompt construction contains anti-repetition and pedagogical progression rules")

# Test 3: fix_plan_data diversifies repetitive notes
mock_repetitive_json = """
{
    "sessions": [
        {"day": "Monday", "start_time": "09:00:00", "end_time": "10:30:00", "subject_name": "Mathématiques", "task_type": "exercise_practice", "notes": "Solve problems 5.1, 5.3; Practice integration by parts"},
        {"day": "Wednesday", "start_time": "14:00:00", "end_time": "15:30:00", "subject_name": "Mathématiques", "task_type": "exercise_practice", "notes": "Solve problems 5.1, 5.3; Practice integration by parts"},
        {"day": "Friday", "start_time": "10:00:00", "end_time": "11:30:00", "subject_name": "Mathématiques", "task_type": "exercise_practice", "notes": "Solve problems 5.1, 5.3; Practice integration by parts"}
    ],
    "total_hours": 4.5,
    "reasoning": "Test plan"
}
"""
parsed = ai._extract_json_from_response(mock_repetitive_json)
assert parsed is not None, "Failed to parse JSON"
sessions = parsed["sessions"]
notes = [s["notes"] for s in sessions]
print(f"[INFO] Diversified notes:\n  1. {notes[0]}\n  2. {notes[1]}\n  3. {notes[2]}")

# Ensure all 3 sessions have distinct notes
assert len(set(notes)) == 3, f"Expected 3 distinct notes, but got duplicates: {notes}"
print("[OK] Notes were successfully diversified across all sessions of the subject!")

print("\nALL AI SERVICE DIVERSITY TESTS PASSED SUCCESSFULLY!")
