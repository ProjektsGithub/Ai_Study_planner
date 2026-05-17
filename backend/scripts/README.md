# Database Scripts

This directory contains utility scripts for database management.

## Scripts

### init_db.py
Initializes the database by creating all tables using SQLAlchemy models.

**Usage:**
```bash
cd backend
.\venv\Scripts\Activate.ps1
python scripts/init_db.py
```

**What it does:**
- Creates all database tables based on SQLAlchemy models
- Sets up indexes and foreign key constraints
- Lists all created tables

### seed_db.py
Seeds the database with development test data.

**Usage:**
```bash
cd backend
.\venv\Scripts\Activate.ps1
python scripts/seed_db.py
```

**What it creates:**
- 1 test user (email: student@example.com, password: password123)
- 1 student profile
- 5 subjects (Algorithms, Database Systems, Web Development, Operating Systems, Software Engineering)
- 9 availability time slots (weekdays 18:00-22:00, weekends morning/afternoon)
- 3 constraints (max daily hours, required breaks, forbidden Friday night slot)
- 1 sample study plan with 7 study sessions

**Test Credentials:**
- Email: `student@example.com`
- Password: `password123`

## Database Setup (First Time)

1. **Install PostgreSQL** (if not already installed)
   ```bash
   # Download from https://www.postgresql.org/download/
   # Or use Laragon's PostgreSQL
   ```

2. **Create database**
   ```sql
   CREATE DATABASE ai_study_planner;
   CREATE USER ai_planner WITH PASSWORD 'your_password';
   GRANT ALL PRIVILEGES ON DATABASE ai_study_planner TO ai_planner;
   ```

3. **Update .env file**
   ```bash
   cp .env.example .env
   # Edit DATABASE_URL in .env
   DATABASE_URL=postgresql://ai_planner:your_password@localhost:5432/ai_study_planner
   ```

4. **Run migrations**
   ```bash
   alembic upgrade head
   ```

5. **Seed database** (optional, for development)
   ```bash
   python scripts/seed_db.py
   ```

## Alembic Migrations

### Create a new migration
```bash
alembic revision --autogenerate -m "Description of changes"
```

### Apply migrations
```bash
alembic upgrade head
```

### Rollback last migration
```bash
alembic downgrade -1
```

### View migration history
```bash
alembic history
```

### View current version
```bash
alembic current
```

## Troubleshooting

### Connection refused
- Ensure PostgreSQL is running
- Check DATABASE_URL in .env
- Verify PostgreSQL is listening on port 5432

### Permission denied
- Check database user permissions
- Ensure user has CREATE, ALTER, DROP privileges

### Migration conflicts
- Check alembic_version table
- Resolve conflicts manually if needed
- Use `alembic stamp head` to mark current version (use with caution)
