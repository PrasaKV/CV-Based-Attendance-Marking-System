# CV-Based Attendance Marking System

A Flask-based web application for marking student attendance using computer vision and signature detection.

## Features

✅ **Image Processing** - Convert attendance sheets to digital records  
✅ **Student Management** - Add, edit, delete student information  
✅ **Attendance History** - Track attendance over time  
✅ **Search & Filter** - Find attendance records by date, student, or status  
✅ **Dashboard** - View statistics and performance metrics  
✅ **Authentication** - Secure login system with session tokens  
✅ **Export Data** - Export to CSV and JSON formats  
✅ **REST API** - Complete API for integration  
✅ **Attendance Alerts** - Identify students below attendance threshold  
✅ **Edit Attendance** - Modify recorded attendance entries  

## Project Structure

```
CV-Based-Attendance-Marking-System/
├── app.py                      # Legacy entry point
├── sams_web.py                 # Legacy attendance manager
├── run.py                       # New application entry point
├── config.py                    # Configuration management
├── services.py                  # Business logic (image processing)
├── database.py                  # Database operations and queries
├── auth.py                      # Authentication and authorization
├── routes.py                    # API endpoints and routes
├── dashboard.py                 # Dashboard and statistics
├── export.py                    # Export utilities
├── requirements.txt             # Python dependencies
├── API_DOCUMENTATION.md         # Complete API reference
├── templates/                   # HTML templates
│   ├── index.html              # Upload page
│   └── results.html            # Results page
├── static/                      # Static files
│   ├── style.css               # Styling
│   └── uploads/                # Uploaded files
└── attendance.db               # SQLite database
```

## Installation

### 1. Clone the Repository
```bash
cd CV-Based-Attendance-Marking-System
```

### 2. Create Virtual Environment
```bash
python -m venv venv

# On Windows
venv\Scripts\activate

# On Linux/Mac
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

## Running the Application

### Development Mode
```bash
python run.py
```

The application will start at `http://localhost:5000`

### Production Mode
```bash
$env:FLASK_ENV="production"
python run.py
```

## Configuration

Edit `config.py` to customize settings:

```python
class Config:
    UPLOAD_FOLDER = os.path.join("static", "uploads")
    DATABASE = "attendance.db"
    SECRET_KEY = "your-secret-key-here"
```

## API Usage

### Quick Start

1. **Register a User**
```bash
curl -X POST http://localhost:5000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "email": "admin@example.com",
    "password": "admin123"
  }'
```

2. **Login**
```bash
curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "password": "admin123"
  }'
```

3. **Use the Token**
```bash
curl -X GET http://localhost:5000/api/students \
  -H "Authorization: Bearer <your_token>"
```

### Available Endpoints

#### Authentication
- `POST /api/auth/register` - Register user
- `POST /api/auth/login` - Login user
- `POST /api/auth/logout` - Logout user

#### Student Management
- `GET /api/students` - Get all students
- `GET /api/students/<index>` - Get student details
- `POST /api/students` - Create student
- `PUT /api/students/<index>` - Update student
- `DELETE /api/students/<index>` - Delete student

#### Attendance
- `GET /api/attendance/records` - Get attendance records
- `GET /api/attendance/date/<date>` - Get by date
- `GET /api/attendance/student/<index>` - Get student history
- `PUT /api/attendance/<id>` - Update attendance

#### Dashboard
- `GET /api/dashboard/overview` - Overview stats
- `GET /api/dashboard/performance` - Student performance
- `GET /api/dashboard/daily/<date>` - Daily summary
- `GET /api/dashboard/trends` - Attendance trends
- `GET /api/dashboard/top-performers` - Top students
- `GET /api/dashboard/alerts` - Low attendance alerts
- `GET /api/dashboard/department` - Department stats

#### Export
- `GET /api/export/attendance` - Export attendance
- `GET /api/export/report` - Export summary report

#### Search
- `GET /api/search/students` - Search students
- `GET /api/search/attendance` - Search attendance

See [API_DOCUMENTATION.md](API_DOCUMENTATION.md) for complete details.

## Web Interface

### Upload Page
- Access at `http://localhost:5000/`
- Upload attendance image and student list
- View marked attendance results

### Results Page
- Shows processing steps (original, grayscale, binarized)
- Displays detected attendance status
- Shows Present/Absent for each student

## Database Schema

### Students Table
```sql
CREATE TABLE students (
    id INTEGER PRIMARY KEY,
    student_index TEXT UNIQUE,
    student_name TEXT,
    email TEXT,
    phone TEXT,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);
```

### Attendance Table
```sql
CREATE TABLE attendance (
    id INTEGER PRIMARY KEY,
    date TEXT,
    student_index TEXT,
    student_name TEXT,
    status TEXT,
    created_at TIMESTAMP
);
```

### Users Table
```sql
CREATE TABLE users (
    id INTEGER PRIMARY KEY,
    username TEXT UNIQUE,
    email TEXT UNIQUE,
    password_hash TEXT,
    role TEXT,
    is_active BOOLEAN,
    created_at TIMESTAMP
);
```

## Key Modules

### `services.py` - AttendanceManager
- `parse_students_text()` - Parse XML student data
- `process_image_web()` - Process attendance sheet image
- `analyze_attendance_web()` - Detect signatures and mark attendance

### `database.py` - Database Operations
- Student CRUD operations
- Attendance record management
- Query and filtering
- Statistics calculation

### `auth.py` - Authentication
- User registration and login
- Password hashing with salt
- Session management
- Token verification

### `dashboard.py` - Analytics
- Overview statistics
- Student performance metrics
- Attendance trends
- Alerts and notifications

### `export.py` - Data Export
- Export to CSV
- Export to JSON
- Generate summary reports

## Workflow Example

1. **Register & Login**
   - Create user account via `/api/auth/register`
   - Get session token via `/api/auth/login`

2. **Manage Students**
   - Add students via `/api/students` POST
   - View students via `/api/students` GET
   - Update via PUT, delete via DELETE

3. **Upload Attendance**
   - Upload image + XML via `/upload` POST
   - System processes image and records attendance

4. **View Reports**
   - Check dashboard via `/api/dashboard/*`
   - Export data via `/api/export/*`
   - Search records via `/api/search/*`

## Troubleshooting

### Import Errors
```bash
pip install --upgrade -r requirements.txt
```

### Database Issues
```bash
# Delete old database to reset
rm attendance.db
python run.py
```

### Port Already in Use
```bash
# Change port in run.py
app.run(host="0.0.0.0", port=5001)
```

## Performance Tips

- Use pagination with `limit` parameter for large datasets
- Cache dashboard statistics for repeated queries
- Clean up old uploaded images periodically
- Optimize image processing for large batches

## Security Notes

- Change `SECRET_KEY` in production
- Use HTTPS in production
- Implement rate limiting
- Validate all user inputs
- Store sensitive data securely

## Future Enhancements

- Real-time attendance marking
- Mobile app integration
- Biometric authentication
- Advanced analytics
- Email notifications
- SMS alerts
- Integration with student information systems

## License

MIT License - Feel free to use this project for educational purposes.

## Support

For issues or questions, please refer to the API documentation or create an issue in the repository.

---

**Version:** 2.0  
**Last Updated:** 2024  
**Python Version:** 3.7+
