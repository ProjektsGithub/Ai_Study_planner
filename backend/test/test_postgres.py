"""
Test PostgreSQL connection and database
"""
import sys
from pathlib import Path

# Add the backend directory to the path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from sqlalchemy import create_engine, text
from app.core.config import settings

def test_postgres_connection():
    """Test PostgreSQL connection"""
    
    print("Testing PostgreSQL connection...")
    print(f"Database URL: {settings.DATABASE_URL}")
    
    try:
        # Create engine
        engine = create_engine(settings.DATABASE_URL)
        
        # Test connection
        with engine.connect() as conn:
            # Get PostgreSQL version
            result = conn.execute(text("SELECT version();"))
            version = result.fetchone()[0]
            print(f"\n✓ PostgreSQL connected successfully!")
            print(f"Version: {version[:80]}...")
            
            # Check if database exists
            result = conn.execute(text("SELECT current_database();"))
            db_name = result.fetchone()[0]
            print(f"Current database: {db_name}")
            
            # List tables
            result = conn.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                ORDER BY table_name;
            """))
            tables = result.fetchall()
            
            print(f"\nTables in database ({len(tables)}):")
            for table in tables:
                print(f"  - {table[0]}")
            
            # Check users table
            result = conn.execute(text("SELECT COUNT(*) FROM users;"))
            user_count = result.fetchone()[0]
            print(f"\nUsers in database: {user_count}")
            
            # List recent users
            if user_count > 0:
                result = conn.execute(text("""
                    SELECT id, email, name, created_at 
                    FROM users 
                    ORDER BY created_at DESC 
                    LIMIT 5;
                """))
                users = result.fetchall()
                print("\nRecent users:")
                for user in users:
                    print(f"  - ID: {user[0]}, Email: {user[1]}, Name: {user[2]}, Created: {user[3]}")
            
            return True
            
    except Exception as e:
        print(f"\n✗ PostgreSQL connection failed!")
        print(f"Error: {e}")
        return False

if __name__ == "__main__":
    success = test_postgres_connection()
    sys.exit(0 if success else 1)
