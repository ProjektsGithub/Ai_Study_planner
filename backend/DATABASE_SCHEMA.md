# Database Schema Documentation

## Overview

The AI Study Planner uses PostgreSQL as its relational database. The schema consists of 9 main tables with well-defined relationships and indexes for optimal performance.

## Entity Relationship Diagram

```
┌─────────────┐
│    User     │
│─────────────│
│ id (PK)     │
│ email       │
│ password_hash│
│ name        │
└──────┬──────┘
       │
       │ 1:1
       ▼
┌─────────────────┐
│ StudentProfile  │
│─────────────────│
│ id (PK)         │
│ user_id (FK)    │
│ cursus          │
│ academic_level  │
│ weekly_study_goal│
│ preferences     │
└─────────────────┘

       │ 1:N
       ├──────────────┬──────────────┬──────────────┬──────────────┐
       ▼              ▼              ▼              ▼              ▼
┌─────────────┐ ┌──────────────┐ ┌─────────────┐ ┌──────────────┐ ┌──────────────┐
│  Subject    │ │ Availability │ │ Constraint  │ │  StudyPlan   │ │GenerationLog │
│─────────────│ │──────────────│ │─────────────│ │──────────────│ │──────────────│
│ id (PK)     │ │ id (PK)      │ │ id (PK)     │ │ id (PK)      │ │ id (PK)      │
│ user_id (FK)│ │ user_id (FK) │ │ user_id (FK)│ │ plan_id (UUID)│ │ user_id (FK) │
│ name        │ │ day_of_week  │ │ type        │ │ user_id (FK) │ │ request_hash │
│ priority    │ │ start_time   │ │ parameters  │ │ week_start   │ │ duration     │
│ difficulty  │ │ end_time     │ │ active      │ │ status       │ │ success      │
│ target_hours│ └──────────────┘ └─────────────┘ │ summary      │ └──────────────┘
│ exam_date   │                                   │ edited       │
└──────┬──────┘                                   └──────┬───────┘
       │                                                 │
       │                                                 │ 1:N
       │                                                 ▼
       │                                          ┌──────────────┐
       │                                          │ StudySession │
       │                                          │──────────────│
       │                                          │ id (PK)      │
       │                                          │ plan_id (FK) │
       └──────────────────────────────────────────│ subject_id(FK)│
                                                  │ day          │
                                                  │ start_time   │
                                                  │ end_time     │
                                                  │ task_type    │
                                                  │ notes        │
                                                  └──────────────┘

       │ 1:N
       ▼
┌──────────────┐
│ Notification │
│──────────────│
│ id (PK)      │
│ user_id (FK) │
│ type         │
│ message      │
│ read         │
└──────────────┘
```

## Tables

### users
Stores user authentication and identity information.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PRIMARY KEY | Unique user identifier |
| email | VARCHAR(255) | UNIQUE, NOT NULL | User email address |
| password_hash | VARCHAR(255) | NOT NULL | Hashed password (Argon2/bcrypt) |
| name | VARCHAR(100) | NOT NULL | User's full name |
| created_at | TIMESTAMP | NOT NULL | Account creation timestamp |
| is_active | BOOLEAN | NOT NULL, DEFAULT TRUE | Account active status |
| failed_login_attempts | INTEGER | NOT NULL, DEFAULT 0 | Failed login counter |
| last_failed_login | TIMESTAMP | NULL | Last failed login timestamp |

**Indexes:**
- `ix_users_id` on `id`
- `ix_users_email` on `email` (UNIQUE)

---

### student_profiles
Stores academic profile and preferences for each user.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PRIMARY KEY | Profile identifier |
| user_id | INTEGER | FOREIGN KEY (users.id), UNIQUE | Reference to user |
| cursus | VARCHAR(100) | NOT NULL | Academic program |
| academic_level | VARCHAR(50) | NOT NULL | Current academic level |
| weekly_study_goal | FLOAT | NOT NULL | Target study hours per week (1-168) |
| preferences | JSON | NULL | User preferences (max 5000 chars) |
| created_at | TIMESTAMP | NOT NULL | Profile creation timestamp |
| updated_at | TIMESTAMP | NOT NULL | Last update timestamp |

**Indexes:**
- `ix_student_profiles_id` on `id`

**Foreign Keys:**
- `user_id` → `users.id` (CASCADE DELETE)

---

### subjects
Stores academic subjects with priorities and exam dates.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PRIMARY KEY | Subject identifier |
| user_id | INTEGER | FOREIGN KEY (users.id) | Reference to user |
| name | VARCHAR(100) | NOT NULL | Subject name |
| priority | INTEGER | NOT NULL | Priority level (1-5) |
| difficulty | INTEGER | NOT NULL | Difficulty level (1-5) |
| target_weekly_hours | FLOAT | NOT NULL | Target hours per week (0.5-168) |
| exam_date | DATE | NULL | Upcoming exam date |
| created_at | TIMESTAMP | NOT NULL | Creation timestamp |

**Indexes:**
- `ix_subjects_id` on `id`
- `ix_subjects_user_id` on `user_id`

**Foreign Keys:**
- `user_id` → `users.id` (CASCADE DELETE)

**Constraints:**
- Maximum 100 subjects per user (enforced at application level)

---

### availabilities
Stores weekly availability time slots.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PRIMARY KEY | Availability identifier |
| user_id | INTEGER | FOREIGN KEY (users.id) | Reference to user |
| day_of_week | VARCHAR(10) | NOT NULL | Day name (Monday-Sunday) |
| start_time | TIME | NOT NULL | Start time (HH:MM) |
| end_time | TIME | NOT NULL | End time (HH:MM) |
| created_at | TIMESTAMP | NOT NULL | Creation timestamp |

**Indexes:**
- `ix_availabilities_id` on `id`
- `ix_availabilities_user_id` on `user_id`

**Foreign Keys:**
- `user_id` → `users.id` (CASCADE DELETE)

**Validation:**
- `start_time` must be before `end_time`
- Overlapping availabilities allowed

---

### constraints
Stores scheduling constraints (forbidden slots, max hours, breaks, fixed slots).

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PRIMARY KEY | Constraint identifier |
| user_id | INTEGER | FOREIGN KEY (users.id) | Reference to user |
| constraint_type | VARCHAR(50) | NOT NULL | Type: forbidden_slot, max_daily_hours, required_break, fixed_slot |
| parameters | JSON | NOT NULL | Type-specific parameters |
| active | BOOLEAN | NOT NULL, DEFAULT TRUE | Active status |
| created_at | TIMESTAMP | NOT NULL | Creation timestamp |

**Indexes:**
- `ix_constraints_id` on `id`
- `ix_constraints_user_id_active` on `(user_id, active)`

**Foreign Keys:**
- `user_id` → `users.id` (CASCADE DELETE)

**Constraint Types & Parameters:**

1. **forbidden_slot**
   ```json
   {
     "day": "Monday",
     "start_time": "12:00",
     "end_time": "14:00"
   }
   ```

2. **max_daily_hours**
   ```json
   {
     "max_hours": 4.0
   }
   ```

3. **required_break**
   ```json
   {
     "break_duration_minutes": 15,
     "break_after_minutes": 90
   }
   ```

4. **fixed_slot**
   ```json
   {
     "day": "Wednesday",
     "start_time": "18:00",
     "end_time": "20:00",
     "subject_id": 5
   }
   ```

**Constraints:**
- Maximum 50 constraints per user (enforced at application level)

---

### study_plans
Stores generated weekly study plans.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PRIMARY KEY | Plan identifier |
| plan_id | VARCHAR(36) | UNIQUE, NOT NULL | UUID for external reference |
| user_id | INTEGER | FOREIGN KEY (users.id) | Reference to user |
| week_start | DATE | NOT NULL | Monday of the week |
| status | VARCHAR(20) | NOT NULL | Status: generated, superseded, outdated |
| summary | TEXT | NULL | AI-generated summary |
| edited | BOOLEAN | NOT NULL, DEFAULT FALSE | Manual edit flag |
| created_at | TIMESTAMP | NOT NULL | Creation timestamp |

**Indexes:**
- `ix_study_plans_id` on `id`
- `ix_study_plans_plan_id` on `plan_id` (UNIQUE)
- `ix_study_plans_user_id` on `user_id`
- `ix_study_plans_week_start` on `week_start`
- `ix_study_plans_status` on `status`

**Foreign Keys:**
- `user_id` → `users.id` (CASCADE DELETE)

**Status Values:**
- `generated`: Active plan
- `superseded`: Replaced by newer plan
- `outdated`: Invalidated by data changes

---

### study_sessions
Stores individual study sessions within a plan.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PRIMARY KEY | Session identifier |
| study_plan_id | INTEGER | FOREIGN KEY (study_plans.id) | Reference to plan |
| subject_id | INTEGER | FOREIGN KEY (subjects.id) | Reference to subject |
| day | VARCHAR(10) | NOT NULL | Day name (Monday-Sunday) |
| start_time | TIME | NOT NULL | Start time (HH:MM) |
| end_time | TIME | NOT NULL | End time (HH:MM) |
| task_type | VARCHAR(20) | NOT NULL | Type: revision, exercises, reading, project, exam_prep |
| notes | TEXT | NULL | Optional notes |

**Indexes:**
- `ix_study_sessions_id` on `id`
- `ix_study_sessions_study_plan_id` on `study_plan_id`

**Foreign Keys:**
- `study_plan_id` → `study_plans.id` (CASCADE DELETE)
- `subject_id` → `subjects.id` (CASCADE DELETE)

**Constraints:**
- Maximum 50 sessions per plan (enforced at application level)
- `start_time` must be before `end_time`

---

### generation_logs
Stores logs of AI service generation requests.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PRIMARY KEY | Log identifier |
| user_id | INTEGER | FOREIGN KEY (users.id) | Reference to user |
| request_hash | VARCHAR(64) | NOT NULL | SHA-256 hash of request |
| duration_seconds | FLOAT | NOT NULL | Generation duration |
| token_count | INTEGER | NULL | Token count (if available) |
| success | BOOLEAN | NOT NULL | Success status |
| error_message | TEXT | NULL | Error message if failed |
| created_at | TIMESTAMP | NOT NULL | Log timestamp |

**Indexes:**
- `ix_generation_logs_id` on `id`
- `ix_generation_logs_user_id` on `user_id`
- `ix_generation_logs_request_hash` on `request_hash`
- `ix_generation_logs_success` on `success`
- `ix_generation_logs_created_at` on `created_at`

**Foreign Keys:**
- `user_id` → `users.id` (CASCADE DELETE)

---

### notifications
Stores user notifications and reminders.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PRIMARY KEY | Notification identifier |
| user_id | INTEGER | FOREIGN KEY (users.id) | Reference to user |
| notification_type | VARCHAR(50) | NOT NULL | Type: plan_generated, session_reminder, system_alert |
| message | VARCHAR(1000) | NOT NULL | Notification message |
| read | BOOLEAN | NOT NULL, DEFAULT FALSE | Read status |
| created_at | TIMESTAMP | NOT NULL | Creation timestamp |

**Indexes:**
- `ix_notifications_id` on `id`
- `ix_notifications_user_id` on `user_id`
- `ix_notifications_notification_type` on `notification_type`
- `ix_notifications_read` on `read`
- `ix_notifications_created_at` on `created_at`

**Foreign Keys:**
- `user_id` → `users.id` (CASCADE DELETE)

**Retention:**
- Notifications older than 30 days are automatically deleted

---

## Data Integrity Rules

### Cascade Deletes
All foreign keys use `CASCADE DELETE` to maintain referential integrity:
- Deleting a user deletes all associated data
- Deleting a subject removes it from all study sessions
- Deleting a study plan removes all its sessions

### Application-Level Constraints
- Maximum 100 subjects per user
- Maximum 50 constraints per user
- Maximum 50 sessions per study plan
- Weekly study goal: 1-168 hours
- Subject priority/difficulty: 1-5 scale
- Subject target hours: 0.5-168 range

### Validation Rules
- Email must be unique and valid (RFC 5322)
- Password must meet complexity requirements (8+ chars, mixed case, digit)
- Time ranges: start_time < end_time
- Exam dates must be in the future
- Constraint parameters must match type schema

---

## Performance Considerations

### Indexes
All frequently queried columns are indexed:
- Primary keys (automatic)
- Foreign keys for join performance
- Email for login lookups
- Status fields for filtering
- Timestamps for sorting and range queries

### Query Optimization
- Use composite index on `(user_id, active)` for constraints
- Use composite index on `(user_id, week_start)` for plan lookups
- Pagination recommended for large result sets

### Connection Pooling
- Pool size: 20 connections
- Max overflow: 0 (no additional connections)
- Pre-ping enabled for connection health checks

---

## Backup and Maintenance

### Recommended Backup Strategy
- Daily full backups
- Point-in-time recovery enabled
- Retention: 30 days minimum

### Maintenance Tasks
- Vacuum analyze weekly
- Reindex monthly
- Delete old notifications (30+ days)
- Delete old generation logs (90+ days)
- Archive old study plans (90+ days)

---

## Migration History

| Version | Date | Description |
|---------|------|-------------|
| 4c065a15bc77 | 2026-05-17 | Initial database schema |

---

*Last Updated: May 17, 2026*
