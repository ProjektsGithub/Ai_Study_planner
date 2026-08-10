"""
Génération de la documentation API en format Markdown
"""
from pathlib import Path

markdown_content = """# 📚 API Documentation - AI Study Planner

**Version:** 1.0.0  
**Base URL:** `http://localhost:8000`  
**Authentication:** JWT Bearer Token

---

## 🔐 Authentication

### Register User
```http
POST /api/v1/auth/register
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "securepassword",
  "full_name": "John Doe"
}
```

**Response (201 Created):**
```json
{
  "id": 1,
  "email": "user@example.com",
  "full_name": "John Doe",
  "created_at": "2026-07-12T10:00:00Z"
}
```

---

### Login User
```http
POST /api/v1/auth/login
Content-Type: application/x-www-form-urlencoded

username=user@example.com&password=securepassword
```

**Response (200 OK):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

---

### Refresh Token
```http
POST /api/v1/auth/refresh
Authorization: Bearer <refresh_token>
```

---

## 👤 Profile

### Get User Profile
```http
GET /api/v1/profile/me
Authorization: Bearer <access_token>
```

**Response (200 OK):**
```json
{
  "id": 1,
  "email": "user@example.com",
  "full_name": "John Doe",
  "student_profile": {
    "id": 1,
    "current_semester": 3,
    "total_ects": 180,
    "completed_ects": 90,
    "study_pace": "full_time"
  }
}
```

---

### Update Profile
```http
PUT /api/v1/profile/me
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "full_name": "John Updated Doe",
  "student_profile": {
    "current_semester": 4
  }
}
```

---

## 📚 Subjects

### List Subjects
```http
GET /api/v1/subjects
Authorization: Bearer <access_token>
```

**Response (200 OK):**
```json
[
  {
    "id": 1,
    "name": "Advanced Mathematics",
    "ects_credits": 6,
    "difficulty": 8,
    "priority": 9,
    "status": "in_progress",
    "semester": 3,
    "exam_date": "2026-08-15"
  }
]
```

---

### Create Subject
```http
POST /api/v1/subjects
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "name": "Machine Learning",
  "ects_credits": 5,
  "difficulty": 9,
  "priority": 10,
  "semester": 4,
  "exam_date": "2026-09-20",
  "hours_per_week": 10
}
```

---

### Update Subject
```http
PUT /api/v1/subjects/{subject_id}
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "difficulty": 7,
  "priority": 8
}
```

---

### Delete Subject
```http
DELETE /api/v1/subjects/{subject_id}
Authorization: Bearer <access_token>
```

---

## 📅 Study Plans

### List Study Plans
```http
GET /api/v1/study-plans
Authorization: Bearer <access_token>
```

---

### Generate Study Plan
```http
POST /api/v1/study-plans/generate
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "week_start": "2026-07-14",
  "preferences": {
    "max_hours_per_day": 8,
    "preferred_study_times": ["morning", "afternoon"]
  }
}
```

**Response (201 Created):**
```json
{
  "id": 1,
  "week_start": "2026-07-14",
  "week_end": "2026-07-20",
  "status": "active",
  "sessions": [
    {
      "id": 1,
      "day_of_week": "monday",
      "start_time": "09:00",
      "end_time": "11:00",
      "subject": {
        "id": 1,
        "name": "Advanced Mathematics"
      },
      "focus_area": "Calculus"
    }
  ],
  "created_at": "2026-07-12T10:00:00Z"
}
```

---

### Get Study Plan
```http
GET /api/v1/study-plans/{plan_id}
Authorization: Bearer <access_token>
```

---

### Export Study Plan to PDF
```http
GET /api/v1/study-plans/{plan_id}/export
Authorization: Bearer <access_token>
```

**Response:** PDF file download

---

## 🕐 Availabilities

### List Availabilities
```http
GET /api/v1/availabilities
Authorization: Bearer <access_token>
```

---

### Create Availability
```http
POST /api/v1/availabilities
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "day_of_week": "monday",
  "start_time": "09:00",
  "end_time": "17:00",
  "is_available": true
}
```

---

## 🚫 Constraints

### List Constraints
```http
GET /api/v1/constraints
Authorization: Bearer <access_token>
```

---

### Create Constraint
```http
POST /api/v1/constraints
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "constraint_type": "max_daily_hours",
  "value": 8,
  "description": "Maximum 8 hours of study per day"
}
```

---

## 📝 Exams

### List Exams
```http
GET /api/v1/exams
Authorization: Bearer <access_token>
```

---

### Create Exam
```http
POST /api/v1/exams
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "subject_id": 1,
  "exam_date": "2026-08-15",
  "exam_time": "14:00",
  "duration_minutes": 180,
  "location": "Amphitheater A",
  "exam_type": "written"
}
```

---

## 📊 Grades

### List Grades
```http
GET /api/v1/grades
Authorization: Bearer <access_token>
```

---

### Record Grade
```http
POST /api/v1/grades
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "subject_id": 1,
  "grade": 15.5,
  "max_grade": 20,
  "exam_date": "2026-08-15",
  "grade_type": "final_exam"
}
```

---

## 📈 ECTS Progress

### Get ECTS Progress
```http
GET /api/v1/ects
Authorization: Bearer <access_token>
```

**Response (200 OK):**
```json
{
  "total_required": 180,
  "completed": 90,
  "in_progress": 30,
  "remaining": 60,
  "completion_percentage": 50.0,
  "current_semester": 3,
  "progression_rate": "on_track"
}
```

---

## 🔔 Notifications

### List Notifications
```http
GET /api/v1/notifications
Authorization: Bearer <access_token>
```

---

### Mark Notification as Read
```http
PUT /api/v1/notifications/{notification_id}/read
Authorization: Bearer <access_token>
```

---

### Delete Notification
```http
DELETE /api/v1/notifications/{notification_id}
Authorization: Bearer <access_token>
```

---

## 🤖 AI Features

### Get AI Context
```http
POST /api/v1/ai-context
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "include_subjects": true,
  "include_exams": true,
  "include_grades": true
}
```

---

### Chat with AI Assistant
```http
POST /api/v1/chat
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "message": "How should I prioritize my subjects this week?",
  "context": "study_planning"
}
```

---

## 🏢 Admin Endpoints (RBAC Required)

### Admin Dashboard
```http
GET /api/v1/admin/dashboard
Authorization: Bearer <admin_token>
```

---

### Universities

#### List Universities
```http
GET /api/v1/admin/universities
Authorization: Bearer <admin_token>
```

#### Create University
```http
POST /api/v1/admin/universities
Authorization: Bearer <admin_token>
Content-Type: application/json

{
  "name": "University of Technology",
  "code": "UNITECH",
  "country": "France",
  "city": "Paris"
}
```

---

### Study Programs

#### List Study Programs
```http
GET /api/v1/admin/study-programs
Authorization: Bearer <admin_token>
```

#### Create Study Program
```http
POST /api/v1/admin/study-programs
Authorization: Bearer <admin_token>
Content-Type: application/json

{
  "name": "Computer Science Bachelor",
  "code": "CS-BSC",
  "degree_level": "bachelor",
  "duration_semesters": 6,
  "total_ects_required": 180,
  "campus_id": 1
}
```

---

### Courses

#### List Courses
```http
GET /api/v1/admin/courses
Authorization: Bearer <admin_token>
```

#### Create Course
```http
POST /api/v1/admin/courses
Authorization: Bearer <admin_token>
Content-Type: application/json

{
  "name": "Algorithms and Data Structures",
  "code": "CS201",
  "ects_credits": 6,
  "semester": 3,
  "is_mandatory": true,
  "study_program_id": 1
}
```

---

### Bulk Import

#### Import Data
```http
POST /api/v1/admin/imports
Authorization: Bearer <admin_token>
Content-Type: multipart/form-data

file=@courses.csv
entity_type=courses
```

**CSV Format (courses.csv):**
```csv
course_code,name,ects_credits,semester,is_mandatory
CS101,Introduction to Programming,6,1,true
CS102,Mathematics for CS,5,1,true
CS201,Algorithms,6,2,true
```

---

### Audit Logs

#### Get Audit Logs
```http
GET /api/v1/admin/audit?user_id=123&limit=50
Authorization: Bearer <admin_token>
```

**Response (200 OK):**
```json
{
  "total": 150,
  "logs": [
    {
      "id": 1,
      "user_id": 5,
      "action": "create",
      "entity_type": "course",
      "entity_id": 42,
      "changes": {
        "name": "New Course"
      },
      "ip_address": "192.168.1.10",
      "timestamp": "2026-07-12T10:00:00Z"
    }
  ]
}
```

---

## 📥 Export Endpoints

### Export Study Plan
```http
GET /api/v1/exports/plan/{plan_id}?format=pdf
Authorization: Bearer <access_token>
```

**Formats disponibles:** `pdf`, `json`, `csv`

---

## ⚠️ Error Responses

### 400 Bad Request
```json
{
  "detail": "Invalid input data",
  "errors": [
    {
      "field": "email",
      "message": "Invalid email format"
    }
  ]
}
```

### 401 Unauthorized
```json
{
  "detail": "Not authenticated"
}
```

### 403 Forbidden
```json
{
  "detail": "Not enough permissions"
}
```

### 404 Not Found
```json
{
  "detail": "Resource not found"
}
```

### 422 Validation Error
```json
{
  "detail": [
    {
      "loc": ["body", "email"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

---

## 🔧 Rate Limiting

- **Rate Limit:** 100 requests per minute per user
- **Headers:**
  - `X-RateLimit-Limit`: Maximum requests allowed
  - `X-RateLimit-Remaining`: Requests remaining
  - `X-RateLimit-Reset`: Time when limit resets (Unix timestamp)

---

## 📌 Notes

- All timestamps are in ISO 8601 format (UTC)
- All dates are in `YYYY-MM-DD` format
- All times are in `HH:MM` format (24-hour)
- Bearer tokens expire after 15 minutes (access) and 7 days (refresh)
- Admin endpoints require `admin` or `super_admin` role

---

## 🚀 Quick Start

1. Register a new user
2. Login to get JWT token
3. Create your profile
4. Add subjects
5. Set availabilities and constraints
6. Generate your first study plan!

---

**For more information, visit the interactive documentation at:**
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
"""

# Sauvegarder le fichier Markdown
output_file = Path("API_DOCUMENTATION.md")
with open(output_file, "w", encoding="utf-8") as f:
    f.write(markdown_content)

print("✅ Documentation Markdown exportée dans API_DOCUMENTATION.md")
print("📄 Ce fichier peut être:")
print("   - Ajouté au repository Git")
print("   - Visualisé sur GitHub avec formatting")
print("   - Converti en PDF avec pandoc")
print("   - Intégré dans un wiki")
