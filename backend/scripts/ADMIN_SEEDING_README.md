# Admin User Seeding Script

This directory contains the seeding script for creating the initial Super Admin account for the Super Admin Platform.

## Overview

The `seed_admin.py` script creates:
1. Three admin role definitions (super_admin, university_admin, program_coordinator)
2. An initial Super Admin user account
3. Role assignment linking the user to the Super Admin role

## Requirements

- PostgreSQL database must be running and configured
- Database connection configured in `.env` file
- Database migrations must be applied (`alembic upgrade head`)

## Usage

### Basic Usage (Default Credentials)

```bash
python scripts/seed_admin.py
```

Default credentials:
- **Email**: admin@example.com
- **Password**: Admin123!
- **Name**: System Administrator

### Custom Credentials

```bash
python scripts/seed_admin.py --email your-admin@example.com --password YourSecurePass123 --name "Your Name"
```

### Command Line Options

- `--email`: Admin email address (default: admin@example.com)
- `--password`: Admin password (default: Admin123!)
- `--name`: Admin full name (default: System Administrator)

## Password Requirements

Passwords must meet the following requirements:
- Minimum 8 characters long
- At least one uppercase letter
- At least one lowercase letter
- At least one digit

## What Gets Created

### 1. Admin Roles

Three role definitions are created:

- **super_admin**: Full system access across all universities and programs
- **university_admin**: Access limited to specific universities
- **program_coordinator**: Access limited to specific programs

### 2. Super Admin User

A user account with:
- Email address
- Hashed password (bcrypt)
- Active status
- Super Admin role assignment

### 3. Role Assignment

A user_role record linking the user to the super_admin role with:
- No university restrictions (university_id = NULL)
- No program restrictions (program_id = NULL)
- Timestamp of assignment

## Authentication Integration

The authentication system has been extended to support role-based access control:

### JWT Token Enhancements

JWT tokens now include role information in the payload:

```json
{
  "sub": "1",
  "exp": 1234567890,
  "type": "access",
  "roles": [
    {
      "role_id": 1,
      "role_name": "super_admin",
      "role_display_name": "Super Admin",
      "university_id": null,
      "program_id": null
    }
  ]
}
```

### Updated Dependencies

The `get_current_user()` dependency now:
1. Validates the JWT token
2. Loads the user from the database
3. Loads user roles from the database (fresh data)
4. Attaches roles to the user object as a dynamic attribute

This ensures role data is always current, even if the token contains outdated role information.

## Example: First-Time Setup

```bash
# 1. Ensure PostgreSQL is running
# 2. Apply database migrations
alembic upgrade head

# 3. Run the seeding script
python scripts/seed_admin.py

# 4. Start the backend server
python -m uvicorn app.main:app --reload

# 5. Login with the credentials provided by the script
# 6. Change the password after first login!
```

## Security Notes

### Change Default Password

**IMPORTANT**: If you use the default credentials, change the password immediately after first login!

### Secure Password Storage

- Passwords are hashed using bcrypt with salt
- Password hashes are never logged or exposed
- Failed login attempts are tracked

### Role Scope

The initial Super Admin account has:
- Full access to all universities (university_id = NULL)
- Full access to all programs (program_id = NULL)
- Permission to create and manage other admin accounts

## Troubleshooting

### User Already Exists

If the email already exists, the script will:
1. Skip user creation
2. Attempt to assign the Super Admin role to the existing user
3. Report success if the user already has the role

### Role Already Exists

If the roles already exist in the database:
- The script will skip role creation
- Role assignments will proceed normally

### Database Connection Errors

Ensure:
1. PostgreSQL is running
2. `.env` file has correct database credentials
3. Database exists and is accessible
4. Migrations have been applied

### Password Validation Errors

If password validation fails:
- Check password meets all requirements (8+ chars, uppercase, lowercase, digit)
- Use single quotes around password if it contains special characters

## Related Files

- `app/core/security.py`: JWT token creation with role support
- `app/core/dependencies.py`: Updated `get_current_user()` dependency
- `app/api/v1/auth.py`: Authentication endpoints with role inclusion
- `app/middleware/rbac.py`: Role-based access control middleware
- `app/models/user_role.py`: User role assignment model
- `app/models/admin_role.py`: Admin role definition model

## Testing

Tests are available in `test/test_admin_auth.py`:

```bash
# Run admin authentication tests
python -m pytest test/test_admin_auth.py -v

# Test cases:
# - Login includes roles in token
# - get_current_user includes roles
# - Refresh token includes roles
# - Users without roles have empty roles list
```

## Next Steps After Seeding

1. **Login**: Use the credentials to login via `/api/v1/auth/login`
2. **Change Password**: Update password via user profile
3. **Create Universities**: Start configuring universities via admin endpoints
4. **Assign Roles**: Create additional admin users with appropriate roles
5. **Configure System**: Set up study programs, courses, and validation rules

## Support

For issues or questions:
1. Check database logs for errors
2. Verify migrations are current: `alembic current`
3. Review `.env` configuration
4. Check backend application logs
