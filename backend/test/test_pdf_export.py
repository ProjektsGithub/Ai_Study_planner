"""
Simple test script for PDF export functionality
"""
import asyncio
from datetime import datetime
from app.core.database import SessionLocal
from app.models.user import User
from app.models.subject import Subject
from app.models.study_plan import StudyPlan
from app.models.study_session import StudySession
from app.services.export_service import ExportService


async def test_pdf_export():
    """Test PDF export with sample data"""
    db = SessionLocal()
    
    try:
        # Find or create test user
        user = db.query(User).filter(User.email == "test_pdf@example.com").first()
        if not user:
            user = User(
                email="test_pdf@example.com",
                full_name="PDF Test User",
                hashed_password="test"
            )
            db.add(user)
            db.commit()
            print(f"✓ Created test user: {user.email}")
        else:
            print(f"✓ Using existing user: {user.email}")
        
        # Create subject
        subject = Subject(
            user_id=user.id,
            name="Mathematics",
            priority=5,
            difficulty=4,
            target_weekly_hours=5.0
        )
        db.add(subject)
        db.commit()
        print(f"✓ Created subject: {subject.name}")
        
        # Create study plan
        plan = StudyPlan(
            user_id=user.id,
            week_start_date=datetime.now().date(),
            total_hours=5.0,
            status="generated"
        )
        db.add(plan)
        db.commit()
        print(f"✓ Created study plan: ID {plan.id}")
        
        # Create sessions
        sessions_data = [
            ("Monday", "09:00", "10:30", "lecture"),
            ("Tuesday", "14:00", "15:30", "exercise"),
            ("Wednesday", "10:00", "11:00", "revision"),
        ]
        
        for day, start, end, task_type in sessions_data:
            session = StudySession(
                study_plan_id=plan.id,
                subject_id=subject.id,
                day=day,
                start_time=start,
                end_time=end,
                task_type=task_type
            )
            db.add(session)
        db.commit()
        print(f"✓ Created {len(sessions_data)} sessions")
        
        # Generate PDF
        print("\n📄 Generating PDF...")
        export_service = ExportService(db)
        pdf_buffer = await export_service.generate_pdf(plan.id, user)
        
        # Save to file
        output_file = "test_study_plan.pdf"
        with open(output_file, "wb") as f:
            f.write(pdf_buffer.getvalue())
        
        # Get file size
        pdf_buffer.seek(0, 2)
        size = pdf_buffer.tell()
        size_kb = size / 1024
        
        print(f"✓ PDF generated successfully!")
        print(f"  - File: {output_file}")
        print(f"  - Size: {size_kb:.2f} KB")
        print(f"  - Max size: {ExportService.MAX_FILE_SIZE / 1024 / 1024:.1f} MB")
        
        # Cleanup
        db.delete(plan)
        db.delete(subject)
        db.commit()
        print(f"\n✓ Cleanup completed")
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


if __name__ == "__main__":
    print("=" * 50)
    print("PDF Export Service Test")
    print("=" * 50)
    print()
    
    asyncio.run(test_pdf_export())
    
    print()
    print("=" * 50)
    print("Test completed!")
    print("=" * 50)
