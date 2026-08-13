# API Documentation - Attendance Marking System

## Overview
This document provides comprehensive API endpoints for the CV-Based Attendance Marking System.

## Base URL
```
http://localhost:5000
```

## Authentication
Most API endpoints require authentication using a Bearer token in the Authorization header:
```
Authorization: Bearer <session_token>
```

---

## Authentication Endpoints

### 1. Register User
**POST** `/api/auth/register`

Register a new user account.

**Request Body:**
```json
{
  "username": "john_doe",
  "email": "john@example.com",
  "password": "secure_password",
  "role": "staff"
}
```

**Response (201):**
```json
{
  "message": "User registered successfully"
}
```

---

### 2. Login
**POST** `/api/auth/login`

Authenticate user and get session token.

**Request Body:**
```json
{
  "username": "john_doe",
  "password": "secure_password"
}
```

**Response (200):**
```json
{
  "message": "Login successful",
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

---

### 3. Logout
**POST** `/api/auth/logout`

Logout user and invalidate session.

**Headers:**
```
Authorization: Bearer <session_token>
```

**Response (200):**
```json
{
  "message": "Logout successful"
}
```

---

## Student Management Endpoints

### 4. Get All Students
**GET** `/api/students`

Retrieve list of all students.

**Headers:**
```
Authorization: Bearer <session_token>
```

**Response (200):**
```json
[
  {
    "id": 1,
    "student_index": "STU001",
    "student_name": "John Doe",
    "email": "john@example.com",
    "phone": "1234567890",
    "created_at": "2024-01-15T10:30:00",
    "updated_at": "2024-01-15T10:30:00"
  }
]
```

---

### 5. Get Student by Index
**GET** `/api/students/<student_index>`

Retrieve specific student details.

**Headers:**
```
Authorization: Bearer <session_token>
```

**Response (200):**
```json
{
  "id": 1,
  "student_index": "STU001",
  "student_name": "John Doe",
  "email": "john@example.com",
  "phone": "1234567890"
}
```

---

### 6. Create Student
**POST** `/api/students`

Add a new student.

**Headers:**
```
Authorization: Bearer <session_token>
```

**Request Body:**
```json
{
  "student_index": "STU002",
  "student_name": "Jane Doe",
  "email": "jane@example.com",
  "phone": "0987654321"
}
```

**Response (201):**
```json
{
  "message": "Student created"
}
```

---

### 7. Update Student
**PUT** `/api/students/<student_index>`

Update student information.

**Headers:**
```
Authorization: Bearer <session_token>
```

**Request Body:**
```json
{
  "student_name": "Jane Smith",
  "email": "jane.smith@example.com",
  "phone": "1111111111"
}
```

**Response (200):**
```json
{
  "message": "Student updated"
}
```

---

### 8. Delete Student
**DELETE** `/api/students/<student_index>`

Delete a student.

**Headers:**
```
Authorization: Bearer <session_token>
```

**Response (200):**
```json
{
  "message": "Student deleted"
}
```

---

## Attendance Management Endpoints

### 9. Get Attendance Records
**GET** `/api/attendance/records`

Retrieve attendance records with optional filters.

**Query Parameters:**
- `date` (optional): Filter by date (YYYY-MM-DD)
- `student_index` (optional): Filter by student index
- `status` (optional): Filter by status (Present/Absent)
- `limit` (optional): Number of records to return (default: 100)

**Headers:**
```
Authorization: Bearer <session_token>
```

**Response (200):**
```json
[
  {
    "id": 1,
    "date": "2024-01-15",
    "student_index": "STU001",
    "student_name": "John Doe",
    "status": "Present",
    "created_at": "2024-01-15T10:30:00"
  }
]
```

---

### 10. Get Attendance by Date
**GET** `/api/attendance/date/<date>`

Get all attendance records for a specific date.

**Headers:**
```
Authorization: Bearer <session_token>
```

**Response (200):**
```json
[
  {
    "id": 1,
    "date": "2024-01-15",
    "student_index": "STU001",
    "student_name": "John Doe",
    "status": "Present"
  }
]
```

---

### 11. Get Student Attendance History
**GET** `/api/attendance/student/<student_index>`

Get attendance history for a specific student.

**Query Parameters:**
- `days` (optional): Number of days to look back (default: 30)

**Headers:**
```
Authorization: Bearer <session_token>
```

**Response (200):**
```json
[
  {
    "date": "2024-01-15",
    "status": "Present"
  },
  {
    "date": "2024-01-14",
    "status": "Absent"
  }
]
```

---

### 12. Update Attendance Status
**PUT** `/api/attendance/<attendance_id>`

Modify an attendance record.

**Headers:**
```
Authorization: Bearer <session_token>
```

**Request Body:**
```json
{
  "status": "Absent"
}
```

**Response (200):**
```json
{
  "message": "Attendance updated"
}
```

---

## Dashboard & Statistics Endpoints

### 13. Get Overview Statistics
**GET** `/api/dashboard/overview`

Get overall attendance statistics.

**Headers:**
```
Authorization: Bearer <session_token>
```

**Response (200):**
```json
{
  "total_records": 450,
  "total_present": 425,
  "total_absent": 25,
  "present_percentage": 94.44,
  "absent_percentage": 5.56
}
```

---

### 14. Get Student Performance
**GET** `/api/dashboard/performance`

Get attendance performance for all students.

**Query Parameters:**
- `days` (optional): Number of days to consider (default: 30)

**Headers:**
```
Authorization: Bearer <session_token>
```

**Response (200):**
```json
[
  {
    "student_index": "STU001",
    "student_name": "John Doe",
    "total_days": 20,
    "present_days": 19,
    "absent_days": 1,
    "attendance_percentage": 95.0
  }
]
```

---

### 15. Get Daily Summary
**GET** `/api/dashboard/daily/<date>`

Get attendance summary for a specific date.

**Headers:**
```
Authorization: Bearer <session_token>
```

**Response (200):**
```json
{
  "date": "2024-01-15",
  "total_students": 50,
  "present": 48,
  "absent": 2,
  "percentage": 96.0
}
```

---

### 16. Get Attendance Trends
**GET** `/api/dashboard/trends`

Get attendance trends over recent days.

**Query Parameters:**
- `days` (optional): Number of days (default: 7)

**Headers:**
```
Authorization: Bearer <session_token>
```

**Response (200):**
```json
[
  {
    "date": "2024-01-10",
    "total_students": 50,
    "present": 46,
    "absent": 4,
    "percentage": 92.0
  },
  {
    "date": "2024-01-15",
    "total_students": 50,
    "present": 48,
    "absent": 2,
    "percentage": 96.0
  }
]
```

---

### 17. Get Top Performers
**GET** `/api/dashboard/top-performers`

Get students with best attendance.

**Query Parameters:**
- `limit` (optional): Number of students (default: 10)
- `days` (optional): Number of days (default: 30)

**Headers:**
```
Authorization: Bearer <session_token>
```

**Response (200):**
```json
[
  {
    "student_index": "STU001",
    "student_name": "John Doe",
    "attendance_percentage": 100.0
  }
]
```

---

### 18. Get Attendance Alerts
**GET** `/api/dashboard/alerts`

Get students below attendance threshold.

**Query Parameters:**
- `threshold` (optional): Attendance threshold (default: 75.0)

**Headers:**
```
Authorization: Bearer <session_token>
```

**Response (200):**
```json
[
  {
    "student_index": "STU005",
    "student_name": "Alex Smith",
    "attendance_percentage": 60.0
  }
]
```

---

### 19. Get Department Statistics
**GET** `/api/dashboard/department`

Get overall department statistics.

**Headers:**
```
Authorization: Bearer <session_token>
```

**Response (200):**
```json
{
  "total_records": 450,
  "total_present": 425,
  "total_absent": 25,
  "total_students": 50,
  "average_attendance_percentage": 94.44
}
```

---

## Export Endpoints

### 20. Export Attendance Data
**GET** `/api/export/attendance`

Export attendance records to CSV or JSON.

**Query Parameters:**
- `date` (optional): Filter by date
- `student_index` (optional): Filter by student
- `status` (optional): Filter by status
- `format` (optional): Export format - csv or json (default: csv)

**Headers:**
```
Authorization: Bearer <session_token>
```

**Response (200):**
File download

---

### 21. Export Summary Report
**GET** `/api/export/report`

Export a summary statistics report.

**Headers:**
```
Authorization: Bearer <session_token>
```

**Response (200):**
Text file download

---

## Search & Filter Endpoints

### 22. Search Students
**GET** `/api/search/students`

Search students by name or index.

**Query Parameters:**
- `q`: Search query

**Headers:**
```
Authorization: Bearer <session_token>
```

**Response (200):**
```json
[
  {
    "student_index": "STU001",
    "student_name": "John Doe"
  }
]
```

---

### 23. Search Attendance Records
**GET** `/api/search/attendance`

Search attendance records with filters.

**Query Parameters:**
- `date` (optional): Filter by date
- `student_index` (optional): Filter by student
- `status` (optional): Filter by status

**Headers:**
```
Authorization: Bearer <session_token>
```

**Response (200):**
```json
[
  {
    "id": 1,
    "date": "2024-01-15",
    "student_index": "STU001",
    "status": "Present"
  }
]
```

---

## File Upload Endpoint

### 24. Upload Attendance
**POST** `/upload`

Upload image and XML file for attendance marking.

**Form Data:**
- `image`: Image file (JPG, PNG)
- `xml`: Student XML file

**Response (200):**
HTML page with results

---

## Error Responses

### 400 Bad Request
```json
{
  "error": "Missing required fields"
}
```

### 401 Unauthorized
```json
{
  "error": "Unauthorized"
}
```

### 404 Not Found
```json
{
  "error": "Resource not found"
}
```

### 500 Internal Server Error
```json
{
  "error": "Internal server error"
}
```

---

## Usage Examples

### Example 1: Login and Get Students
```bash
# Login
curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "john_doe",
    "password": "password123"
  }'

# Get token from response, then use it
curl -X GET http://localhost:5000/api/students \
  -H "Authorization: Bearer <token>"
```

### Example 2: Export Attendance Data
```bash
curl -X GET "http://localhost:5000/api/export/attendance?format=csv&date=2024-01-15" \
  -H "Authorization: Bearer <token>" \
  -o attendance.csv
```

### Example 3: Get Attendance Alerts
```bash
curl -X GET "http://localhost:5000/api/dashboard/alerts?threshold=75" \
  -H "Authorization: Bearer <token>"
```

---

## Notes
- All timestamps are in ISO 8601 format
- Authentication tokens expire after 24 hours
- Dates should be in YYYY-MM-DD format
- Pagination is recommended for large datasets using the `limit` parameter
