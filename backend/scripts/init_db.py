"""
Database initialization script
Creates all tables using SQLAlchemy models
"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.core.database import Base, engine
from app.models import (
    User,
    StudentProfile,
    Subject,
    Availability,
    Constraint,
    StudyPlan,
    StudySession,
    GenerationLog,
    Notification,
)


def init_database():
    """Initialize database by creating all tables"""
    print("Creating database tables...")
    
    try:
        # Create all tables
        Base.metadata.create_all(bind=engine)
        print("✓ All tables created successfully!")
        
        # List created tables
        print("\nCreated tables:")
        for table in Base.metadata.sorted_tables:
            print(f"  - {table.name}")
            
    except Exception as e:
        print(f"✗ Error creating tables: {e}")
        sys.exit(1)


if __name__ == "__main__":
    init_database()
