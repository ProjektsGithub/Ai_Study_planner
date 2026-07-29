"""
Generate synthetic training data for LoRA fine-tuning of study planner AI.

This script creates diverse examples of study schedule generation tasks
in JSONL format suitable for fine-tuning Llama 3.1-8B with Unsloth.
"""
import json
import random
from datetime import datetime, timedelta
from typing import List, Dict, Any


# Sample data pools
SUBJECTS_POOL = [
    "Mathematics", "Physics", "Chemistry", "Biology", "Computer Science",
    "English", "French", "Spanish", "German", "History", "Geography",
    "Economics", "Marketing", "Finance", "Accounting", "Management",
    "Psychology", "Sociology", "Philosophy", "Law", "Medicine",
    "Engineering", "Architecture", "Art History", "Music Theory",
    "Statistics", "Data Science", "Machine Learning", "Web Development",
    "Mobile Development", "Database Systems", "Operating Systems",
    "Networks", "Security", "Algorithms", "Software Engineering"
]

TASK_TYPES = ["lecture_review", "exercise_practice", "exam_preparation", "project_work", "reading"]

DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]


def generate_system_prompt() -> str:
    """Generate consistent system prompt."""
    return "You are a JSON API that generates study schedules. You MUST respond with ONLY valid JSON. Rules: First character: {, Last character: }, NO markdown, NO explanations, Put reasoning INSIDE the \"reasoning\" field."


def generate_subjects(count: int) -> List[Dict[str, Any]]:
    """Generate random subjects with characteristics."""
    selected = random.sample(SUBJECTS_POOL, min(count, len(SUBJECTS_POOL)))
    subjects = []
    
    for i, name in enumerate(selected):
        exam_date = datetime.now() + timedelta(days=random.randint(7, 60))
        subjects.append({
            "name": name,
            "priority": random.choice(["low", "medium", "high"]),
            "difficulty": random.randint(1, 5),
            "exam_date": exam_date.strftime("%Y-%m-%d"),
            "ects": random.choice([2, 3, 4, 5, 6, 7, 8])
        })
    
    return subjects


def generate_available_slots() -> Dict[str, List[str]]:
    """Generate random available time slots."""
    num_days = random.randint(2, 7)
    days = random.sample(DAYS, num_days)
    
    slots = {}
    for day in days:
        # Random time slot patterns
        pattern = random.choice([
            ["09:00-17:00"],
            ["08:00-12:00"],
            ["14:00-18:00"],
            ["09:00-12:00", "14:00-17:00"],
            ["18:00-22:00"]
        ])
        slots[day] = pattern
    
    return slots


def format_user_prompt(subjects: List[Dict], slots: Dict[str, List[str]], 
                       weekly_goal: int, constraints: Dict) -> str:
    """Format the user prompt."""
    prompt = f"Generate a weekly study schedule.\n\nWEEKLY STUDY GOAL: {weekly_goal} hours\n\n"
    
    prompt += "AVAILABLE TIME SLOTS:\n"
    for day, times in slots.items():
        prompt += f"- {day}: {', '.join(times)}\n"
    
    prompt += f"\nSUBJECTS ({len(subjects)} total):\n"
    for i, subj in enumerate(subjects, 1):
        prompt += f"{i}. {subj['name']} (priority: {subj['priority']}, difficulty: {subj['difficulty']}/5, exam: {subj['exam_date']}, ECTS: {subj['ects']})\n"
    
    prompt += f"\nCONSTRAINTS:\n"
    prompt += f"- Max {constraints['max_daily_hours']} hours per day\n"
    prompt += f"- {constraints['break_duration']}min break after {constraints['break_after']}min study\n"
    if constraints.get('require_practice'):
        prompt += "- Must include exercise_practice for each subject\n"
    
    prompt += "\nGenerate JSON."
    
    return prompt


def generate_sessions(subjects: List[Dict], slots: Dict[str, List[str]], 
                     weekly_goal: int, constraints: Dict) -> List[Dict]:
    """Generate realistic study sessions."""
    sessions = []
    hours_allocated = 0
    target_hours = weekly_goal
    
    # Sort subjects by priority and exam proximity
    prioritized_subjects = sorted(subjects, 
                                 key=lambda s: (
                                     0 if s['priority'] == 'high' else (1 if s['priority'] == 'medium' else 2),
                                     s['exam_date']
                                 ))
    
    for day, time_ranges in slots.items():
        for time_range in time_ranges:
            start_str, end_str = time_range.split('-')
            current_time = datetime.strptime(start_str, "%H:%M")
            end_time = datetime.strptime(end_str, "%H:%M")
            
            while current_time < end_time and hours_allocated < target_hours:
                # Pick a subject
                subject = random.choice(prioritized_subjects[:max(2, len(prioritized_subjects)//2)])
                
                # Random session duration (1-3 hours)
                duration_minutes = random.choice([60, 90, 120, 150, 180])
                session_end = current_time + timedelta(minutes=duration_minutes)
                
                if session_end > end_time:
                    break
                
                # Random task type
                task_type = random.choice(TASK_TYPES)
                
                # Generate specific notes
                notes = generate_notes(subject['name'], task_type)
                
                sessions.append({
                    "day": day,
                    "start_time": current_time.strftime("%H:%M:%S"),
                    "end_time": session_end.strftime("%H:%M:%S"),
                    "subject_name": subject['name'],
                    "task_type": task_type,
                    "notes": notes
                })
                
                hours_allocated += duration_minutes / 60
                
                # Add break
                current_time = session_end + timedelta(minutes=constraints['break_duration'])
    
    return sessions


def generate_notes(subject: str, task_type: str) -> str:
    """Generate specific study notes."""
    if task_type == "lecture_review":
        return f"Review {random.choice(['chapters', 'lectures', 'modules'])} {random.randint(1, 5)}-{random.randint(6, 10)}"
    elif task_type == "exercise_practice":
        return f"Solve problems {random.randint(1, 10)}.{random.randint(1, 9)}-{random.randint(1, 10)}.{random.randint(10, 20)}"
    elif task_type == "exam_preparation":
        return "Mock exam practice and review weak areas"
    elif task_type == "project_work":
        return f"Work on project milestone {random.randint(1, 5)}"
    else:
        return f"Read textbook pages {random.randint(50, 100)}-{random.randint(101, 200)}"


def generate_reasoning(subjects: List[Dict], sessions: List[Dict], weekly_goal: int) -> str:
    """Generate reasoning text."""
    high_priority = [s['name'] for s in subjects if s['priority'] == 'high']
    total_hours = sum((datetime.strptime(s['end_time'], "%H:%M:%S") - 
                      datetime.strptime(s['start_time'], "%H:%M:%S")).seconds / 3600 
                     for s in sessions)
    
    reasoning = f"Priority given to "
    if high_priority:
        reasoning += f"{', '.join(high_priority[:2])} (high priority). "
    reasoning += f"Sessions distributed across available days with breaks. "
    reasoning += f"Total {total_hours:.1f} hours allocated."
    
    return reasoning


def generate_example() -> Dict:
    """Generate one complete training example."""
    # Random parameters
    num_subjects = random.randint(2, 8)
    weekly_goal = random.randint(10, 40)
    
    subjects = generate_subjects(num_subjects)
    slots = generate_available_slots()
    constraints = {
        "max_daily_hours": random.choice([6, 8, 10]),
        "break_after": random.choice([60, 90, 120]),
        "break_duration": random.choice([10, 15, 20]),
        "require_practice": random.choice([True, False])
    }
    
    # Generate sessions
    sessions = generate_sessions(subjects, slots, weekly_goal, constraints)
    
    # Calculate total hours
    total_hours = sum((datetime.strptime(s['end_time'], "%H:%M:%S") - 
                      datetime.strptime(s['start_time'], "%H:%M:%S")).seconds / 3600 
                     for s in sessions)
    
    # Generate reasoning
    reasoning = generate_reasoning(subjects, sessions, weekly_goal)
    
    # Build user prompt
    user_prompt = format_user_prompt(subjects, slots, weekly_goal, constraints)
    
    # Build assistant response (pure JSON)
    assistant_response = json.dumps({
        "sessions": sessions,
        "total_hours": round(total_hours, 1),
        "reasoning": reasoning
    }, ensure_ascii=False)
    
    # Build conversation
    return {
        "conversations": [
            {"from": "system", "value": generate_system_prompt()},
            {"from": "user", "value": user_prompt},
            {"from": "assistant", "value": assistant_response}
        ]
    }


def main():
    """Generate training dataset."""
    num_examples = 3000
    output_file = "study_planner_train.jsonl"
    
    print(f"Generating {num_examples} training examples...")
    
    with open(output_file, 'w', encoding='utf-8') as f:
        for i in range(num_examples):
            example = generate_example()
            f.write(json.dumps(example, ensure_ascii=False) + '\n')
            
            if (i + 1) % 50 == 0:
                print(f"Generated {i + 1}/{num_examples} examples")
    
    print(f"✅ Training data saved to {output_file}")
    print(f"📊 Total examples: {num_examples}")
    print(f"💾 File size: {round(os.path.getsize(output_file) / 1024 / 1024, 2)} MB")


if __name__ == "__main__":
    import os
    main()
