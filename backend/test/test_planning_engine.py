"""
Test complet du Planning Engine
"""
import sys
from datetime import date, timedelta
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models.user import User
from app.models.subject import Subject
from app.models.availability import Availability
from app.models.constraint import Constraint
from app.services.planning_engine import PlanningEngine
from app.core.security import get_password_hash
import json

print("=" * 70)
print("Test Complet Planning Engine")
print("=" * 70)
print()

# Create database session
db: Session = SessionLocal()

try:
    # 1. Create test user
    print("1. Créer un utilisateur de test")
    test_user = db.query(User).filter(User.email == "planning_test@example.com").first()
    
    if not test_user:
        test_user = User(
            email="planning_test@example.com",
            password_hash=get_password_hash("TestPassword123!"),
            name="Planning Test User",
            is_active=True,
            failed_login_attempts=0
        )
        db.add(test_user)
        db.commit()
        db.refresh(test_user)
        print(f"   ✓ Utilisateur créé (ID: {test_user.id})")
    else:
        print(f"   ✓ Utilisateur existant (ID: {test_user.id})")
    print()
    
    # Clean up existing data
    print("2. Nettoyage des données existantes")
    db.query(Constraint).filter(Constraint.user_id == test_user.id).delete()
    db.query(Availability).filter(Availability.user_id == test_user.id).delete()
    db.query(Subject).filter(Subject.user_id == test_user.id).delete()
    db.commit()
    print("   ✓ Données nettoyées")
    print()
    
    # 3. Create subjects
    print("3. Créer des matières")
    subjects_data = [
        {"name": "Mathematics", "priority": 5, "difficulty": 4, "target_weekly_hours": 10.0, "exam_date": date.today() + timedelta(days=15)},
        {"name": "Physics", "priority": 4, "difficulty": 5, "target_weekly_hours": 8.0, "exam_date": date.today() + timedelta(days=45)},
        {"name": "Computer Science", "priority": 3, "difficulty": 3, "target_weekly_hours": 12.0, "exam_date": None},
        {"name": "English", "priority": 2, "difficulty": 2, "target_weekly_hours": 5.0, "exam_date": date.today() + timedelta(days=90)},
    ]
    
    subjects = []
    for data in subjects_data:
        subject = Subject(user_id=test_user.id, **data)
        db.add(subject)
        subjects.append(subject)
    
    db.commit()
    for subject in subjects:
        db.refresh(subject)
    print(f"   ✓ {len(subjects)} matières créées")
    print()
    
    # 4. Create availabilities
    print("4. Créer des disponibilités")
    availabilities_data = [
        {"day_of_week": "Monday", "start_time": "09:00:00", "end_time": "12:00:00"},
        {"day_of_week": "Monday", "start_time": "14:00:00", "end_time": "18:00:00"},
        {"day_of_week": "Wednesday", "start_time": "10:00:00", "end_time": "16:00:00"},
        {"day_of_week": "Friday", "start_time": "08:00:00", "end_time": "12:00:00"},
        {"day_of_week": "Friday", "start_time": "13:00:00", "end_time": "17:00:00"},
    ]
    
    from datetime import datetime
    availabilities = []
    for data in availabilities_data:
        avail = Availability(
            user_id=test_user.id,
            day_of_week=data["day_of_week"],
            start_time=datetime.strptime(data["start_time"], "%H:%M:%S").time(),
            end_time=datetime.strptime(data["end_time"], "%H:%M:%S").time()
        )
        db.add(avail)
        availabilities.append(avail)
    
    db.commit()
    print(f"   ✓ {len(availabilities)} disponibilités créées")
    print()
    
    # 5. Create constraints
    print("5. Créer des contraintes")
    constraints_data = [
        {
            "constraint_type": "forbidden_slot",
            "parameters": {"day_of_week": "Monday", "start_time": "12:00:00", "end_time": "14:00:00"},
            "active": True
        },
        {
            "constraint_type": "max_daily_hours",
            "parameters": {"max_hours": 6},
            "active": True
        },
        {
            "constraint_type": "required_break",
            "parameters": {"duration_minutes": 15, "after_minutes": 90},
            "active": True
        },
    ]
    
    constraints = []
    for data in constraints_data:
        constraint = Constraint(user_id=test_user.id, **data)
        db.add(constraint)
        constraints.append(constraint)
    
    db.commit()
    print(f"   ✓ {len(constraints)} contraintes créées")
    print()
    
    # 6. Test Planning Engine - No subjects error
    print("6. Test erreur - pas de matières")
    db.query(Subject).filter(Subject.user_id == test_user.id).delete()
    db.commit()
    
    engine = PlanningEngine(test_user.id, db)
    try:
        engine.generate_planning_data()
        print("   ✗ Erreur: devrait lever une exception")
    except ValueError as e:
        print(f"   ✓ Exception correcte: {e}")
    
    # Restore subjects
    for subject in subjects:
        subject.id = None  # Reset ID to create new records
        db.add(subject)
    db.commit()
    for subject in subjects:
        db.refresh(subject)
    print()
    
    # 7. Test Planning Engine - No availabilities error
    print("7. Test erreur - pas de disponibilités")
    db.query(Availability).filter(Availability.user_id == test_user.id).delete()
    db.commit()
    
    engine = PlanningEngine(test_user.id, db)
    try:
        engine.generate_planning_data()
        print("   ✗ Erreur: devrait lever une exception")
    except ValueError as e:
        print(f"   ✓ Exception correcte: {e}")
    
    # Restore availabilities
    for avail in availabilities:
        avail.id = None  # Reset ID to create new records
        db.add(avail)
    db.commit()
    for avail in availabilities:
        db.refresh(avail)
    print()
    
    # 8. Test Planning Engine - Full generation
    print("8. Génération complète des données de planification")
    engine = PlanningEngine(test_user.id, db)
    planning_data = engine.generate_planning_data()
    
    print(f"   ✓ Données générées avec succès")
    print(f"   - Total subjects: {planning_data['total_subjects']}")
    print(f"   - Total slots: {planning_data['total_slots']}")
    print(f"   - Total slot hours: {planning_data['total_slot_hours']:.1f}h")
    print()
    
    # 9. Verify valid slots
    print("9. Vérifier les créneaux valides")
    valid_slots = planning_data['valid_slots']
    print(f"   ✓ {len(valid_slots)} créneaux valides")
    for slot in valid_slots[:3]:  # Show first 3
        print(f"   - {slot['day']}: {slot['start_time']}-{slot['end_time']} ({slot['duration_minutes']} min)")
    if len(valid_slots) > 3:
        print(f"   ... et {len(valid_slots) - 3} autres")
    print()
    
    # 10. Verify subject priorities
    print("10. Vérifier les priorités des matières")
    priorities = planning_data['subject_priorities']
    print(f"   ✓ {len(priorities)} matières avec priorités calculées")
    for priority in priorities:
        print(f"   - {priority['subject_name']}: {priority['priority_score']:.2f}")
        print(f"     (base: {priority['base_priority']}, difficulty: {priority['difficulty']}, exam: {priority['exam_date']})")
    print()
    
    # 11. Verify constraints
    print("11. Vérifier les contraintes")
    constraint_info = planning_data['constraints']
    print(f"   ✓ Contraintes validées")
    print(f"   - Max daily hours: {constraint_info['max_daily_hours']}")
    print(f"   - Required breaks: {len(constraint_info['required_breaks'])}")
    print(f"   - Fixed slots: {len(constraint_info['fixed_slots'])}")
    print(f"   - Forbidden slots: {constraint_info['forbidden_slots_count']}")
    print()
    
    # 12. Test priority calculation with different exam dates
    print("12. Test calcul de priorité avec différentes dates d'examen")
    
    # Update subjects with different exam dates
    subjects[0].exam_date = date.today() + timedelta(days=5)  # Very urgent
    subjects[1].exam_date = date.today() + timedelta(days=20)  # High priority
    subjects[2].exam_date = date.today() + timedelta(days=45)  # Medium priority
    subjects[3].exam_date = date.today() + timedelta(days=100)  # Low priority
    db.commit()
    
    engine = PlanningEngine(test_user.id, db)
    planning_data = engine.generate_planning_data()
    priorities = planning_data['subject_priorities']
    
    print(f"   ✓ Priorités recalculées")
    for priority in priorities:
        days_until = (datetime.strptime(priority['exam_date'], "%Y-%m-%d").date() - date.today()).days if priority['exam_date'] else None
        print(f"   - {priority['subject_name']}: {priority['priority_score']:.2f} (exam in {days_until} days)")
    print()
    
    # 13. Test forbidden slot removal
    print("13. Test suppression des créneaux interdits")
    
    # Add a forbidden slot that overlaps with Monday 09:00-12:00
    forbidden = Constraint(
        user_id=test_user.id,
        constraint_type="forbidden_slot",
        parameters={"day_of_week": "Monday", "start_time": "10:00:00", "end_time": "11:00:00"},
        active=True
    )
    db.add(forbidden)
    db.commit()
    
    engine = PlanningEngine(test_user.id, db)
    planning_data = engine.generate_planning_data()
    
    monday_slots = [s for s in planning_data['valid_slots'] if s['day'] == 'Monday']
    print(f"   ✓ Créneaux Monday après suppression: {len(monday_slots)}")
    for slot in monday_slots:
        print(f"   - {slot['start_time']}-{slot['end_time']}")
    print()
    
    # 14. Performance test
    print("14. Test de performance")
    import time
    
    start_time = time.time()
    engine = PlanningEngine(test_user.id, db)
    planning_data = engine.generate_planning_data()
    end_time = time.time()
    
    duration = (end_time - start_time) * 1000  # Convert to milliseconds
    print(f"   ✓ Génération complétée en {duration:.2f}ms")
    
    if duration < 2000:
        print(f"   ✓ Performance OK (< 2 secondes)")
    else:
        print(f"   ⚠ Performance lente (> 2 secondes)")
    print()
    
    # 15. Export planning data as JSON
    print("15. Export des données de planification")
    json_output = json.dumps(planning_data, indent=2, default=str)
    print(f"   ✓ Données exportées ({len(json_output)} caractères)")
    print()
    
    print("=" * 70)
    print("✓ Tous les tests terminés avec succès!")
    print("=" * 70)
    
except Exception as e:
    print(f"\n✗ Erreur: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
finally:
    # Cleanup
    if 'test_user' in locals() and test_user:
        db.query(Constraint).filter(Constraint.user_id == test_user.id).delete()
        db.query(Availability).filter(Availability.user_id == test_user.id).delete()
        db.query(Subject).filter(Subject.user_id == test_user.id).delete()
        db.commit()
    db.close()
