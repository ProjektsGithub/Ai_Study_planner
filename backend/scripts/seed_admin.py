"""
Admin user seeding script for creating initial Super Admin account

This script creates the initial Super Admin account that can be used to
configure the Super Admin Platform. It should be run once during initial
system setup.

Requirements: 11.1-11.9, 15.3

Usage:
    python scripts/seed_admin.py
    
    Or with custom credentials:
    python scripts/seed_admin.py --email admin@example.com --password MySecurePass123 --name "Admin User"
"""
import sys
import argparse
from pathlib import Path
from datetime import datetime, timezone

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.core.security import get_password_hash, validate_password_strength
from app.models.user import User
from app.models.admin_role import AdminRole
from app.models.user_role import UserRole


def create_admin_roles(db: Session) -> None:
    """
    Create the three admin role definitions if they don't exist.
    
    Requirements: 11.1, 11.2, 11.3
    
    Roles:
        - super_admin: Full system access across all universities
        - university_admin: Access limited to specific universities
        - program_coordinator: Access limited to specific programs
    """
    roles_data = [
        {
            "name": "super_admin",
            "display_name": "Super Admin",
            "description": "Full system access across all universities and programs. Can manage all administrative functions."
        },
        {
            "name": "university_admin",
            "display_name": "University Admin",
            "description": "Access limited to specific universities. Can manage programs, courses, and curriculum data for assigned universities."
        },
        {
            "name": "program_coordinator",
            "display_name": "Program Coordinator",
            "description": "Access limited to specific programs. Can manage courses, prerequisites, and validation rules for assigned programs."
        }
    ]
    
    created_roles = []
    
    for role_data in roles_data:
        # Check if role already exists
        existing_role = db.query(AdminRole).filter(AdminRole.name == role_data["name"]).first()
        
        if not existing_role:
            role = AdminRole(
                name=role_data["name"],
                display_name=role_data["display_name"],
                description=role_data["description"],
                is_active=True,
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc)
            )
            db.add(role)
            created_roles.append(role_data["name"])
            print(f"  ✓ Created role: {role_data['display_name']}")
        else:
            print(f"  - Role already exists: {role_data['display_name']}")
    
    if created_roles:
        db.commit()
        print(f"\n✓ Created {len(created_roles)} new role(s)")
    else:
        print("\n- All roles already exist")


def create_super_admin(db: Session, email: str, password: str, name: str) -> User:
    """
    Create a Super Admin user account.
    
    Requirements: 11.1, 15.3
    
    Args:
        db: Database session
        email: Admin email address
        password: Admin password (will be hashed)
        name: Admin full name
        
    Returns:
        Created User object
        
    Raises:
        ValueError: If email already exists or password is weak
    """
    # Check if user already exists
    existing_user = db.query(User).filter(User.email == email).first()
    if existing_user:
        raise ValueError(f"User with email '{email}' already exists")
    
    # Validate password strength
    is_valid, error_message = validate_password_strength(password)
    if not is_valid:
        raise ValueError(f"Password validation failed: {error_message}")
    
    # Create user
    password_hash = get_password_hash(password)
    user = User(
        email=email,
        password_hash=password_hash,
        name=name,
        created_at=datetime.now(timezone.utc),
        is_active=True,
        failed_login_attempts=0
    )
    
    db.add(user)
    db.flush()  # Get user ID
    
    print(f"  ✓ Created user: {name} ({email})")
    
    return user


def assign_super_admin_role(db: Session, user: User) -> None:
    """
    Assign Super Admin role to a user.
    
    Requirements: 11.1, 11.4
    
    Args:
        db: Database session
        user: User to assign role to
    """
    # Get super_admin role
    super_admin_role = db.query(AdminRole).filter(
        AdminRole.name == "super_admin"
    ).first()
    
    if not super_admin_role:
        raise ValueError("Super Admin role not found. Roles must be created first.")
    
    # Check if user already has this role
    existing_role = db.query(UserRole).filter(
        UserRole.user_id == user.id,
        UserRole.role_id == super_admin_role.id
    ).first()
    
    if existing_role:
        print(f"  - User already has Super Admin role")
        return
    
    # Assign role (Super Admin has no university or program restrictions)
    user_role = UserRole(
        user_id=user.id,
        role_id=super_admin_role.id,
        university_id=None,  # Super Admin has access to all universities
        program_id=None,      # Super Admin has access to all programs
        assigned_at=datetime.now(timezone.utc),
        assigned_by=None      # Initial admin has no assigner
    )
    
    db.add(user_role)
    db.commit()
    
    print(f"  ✓ Assigned Super Admin role to {user.name}")


def seed_admin_user(email: str = "admin@example.com", 
                   password: str = "Admin123!", 
                   name: str = "System Administrator") -> None:
    """
    Main function to seed the initial Super Admin account.
    
    Requirements: 11.1-11.9, 15.3
    
    Args:
        email: Admin email address
        password: Admin password
        name: Admin full name
    """
    db: Session = SessionLocal()
    
    try:
        print("\n" + "="*60)
        print("  Super Admin Account Setup")
        print("="*60)
        print()
        
        # Step 1: Create admin role definitions
        print("Step 1: Creating admin role definitions...")
        create_admin_roles(db)
        print()
        
        # Step 2: Create Super Admin user
        print("Step 2: Creating Super Admin user...")
        try:
            user = create_super_admin(db, email, password, name)
        except ValueError as e:
            print(f"  ✗ Error: {e}")
            # If user exists, try to get it and assign role
            user = db.query(User).filter(User.email == email).first()
            if user:
                print(f"  - Using existing user: {user.name}")
            else:
                raise
        print()
        
        # Step 3: Assign Super Admin role
        print("Step 3: Assigning Super Admin role...")
        assign_super_admin_role(db, user)
        print()
        
        # Success summary
        print("="*60)
        print("  ✓ Super Admin Account Setup Complete!")
        print("="*60)
        print()
        print("Login Credentials:")
        print(f"  Email:    {email}")
        print(f"  Password: {password}")
        print()
        print("Security Note:")
        print("  Please change the password after first login!")
        print()
        print("Next Steps:")
        print("  1. Start the backend server")
        print("  2. Login with the credentials above")
        print("  3. Change your password in the user profile")
        print("  4. Begin configuring universities and programs")
        print()
        
    except Exception as e:
        db.rollback()
        print()
        print("="*60)
        print("  ✗ Error During Setup")
        print("="*60)
        print(f"  {str(e)}")
        print()
        sys.exit(1)
    finally:
        db.close()


def main():
    """Parse command line arguments and run seeding."""
    parser = argparse.ArgumentParser(
        description="Create initial Super Admin account for the Super Admin Platform"
    )
    parser.add_argument(
        "--email",
        default="admin@example.com",
        help="Admin email address (default: admin@example.com)"
    )
    parser.add_argument(
        "--password",
        default="Admin123!",
        help="Admin password (default: Admin123!)"
    )
    parser.add_argument(
        "--name",
        default="System Administrator",
        help="Admin full name (default: System Administrator)"
    )
    
    args = parser.parse_args()
    
    seed_admin_user(
        email=args.email,
        password=args.password,
        name=args.name
    )


if __name__ == "__main__":
    main()
