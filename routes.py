"""
Routes for the attendance marking system
"""
import os
from functools import wraps
from flask import Blueprint, render_template, request, jsonify, send_file
from services import AttendanceManager
from database import Database
from auth import AuthManager
from dashboard import DashboardManager
from export import ExportManager
from config import Config

# Create blueprint
attendance_bp = Blueprint(
    "attendance",
    __name__,
    url_prefix="/"
)

# Initialize managers
db = Database()
auth_manager = AuthManager(db)
dashboard_manager = DashboardManager(db)


# Authentication decorator
def require_auth(f):
    """Require authentication for protected routes"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        session_token = request.headers.get("Authorization", "").replace("Bearer ", "")
        session = auth_manager.verify_session(session_token)
        
        if not session:
            return jsonify({"error": "Unauthorized"}), 401
        
        return f(*args, **kwargs)
    return decorated_function


# ==================== Authentication Routes ====================

@attendance_bp.route("/api/auth/register", methods=["POST"])
def register():
    """Register a new user"""
    data = request.get_json()
    
    if not data or not data.get("username") or not data.get("password") or not data.get("email"):
        return jsonify({"error": "Missing required fields"}), 400
    
    if auth_manager.register_user(
        data["username"],
        data["email"],
        data["password"],
        data.get("role", "staff")
    ):
        return jsonify({"message": "User registered successfully"}), 201
    
    return jsonify({"error": "Registration failed"}), 400


@attendance_bp.route("/api/auth/login", methods=["POST"])
def login():
    """User login"""
    data = request.get_json()
    
    if not data or not data.get("username") or not data.get("password"):
        return jsonify({"error": "Missing credentials"}), 400
    
    session_token = auth_manager.login(data["username"], data["password"])
    
    if session_token:
        return jsonify({
            "message": "Login successful",
            "token": session_token
        }), 200
    
    return jsonify({"error": "Invalid credentials"}), 401


@attendance_bp.route("/api/auth/logout", methods=["POST"])
@require_auth
def logout():
    """User logout"""
    session_token = request.headers.get("Authorization", "").replace("Bearer ", "")
    
    if auth_manager.logout(session_token):
        return jsonify({"message": "Logout successful"}), 200
    
    return jsonify({"error": "Logout failed"}), 400


# ==================== Upload & Processing Routes ====================

@attendance_bp.route("/", methods=["GET"])
def index():
    """Render the main upload page"""
    return render_template("index.html")


@attendance_bp.route("/upload", methods=["POST"])
def upload():
    """Handle file upload and process attendance"""
    # Validate uploaded files
    if "image" not in request.files or "xml" not in request.files:
        return "Missing files", 400

    image_file = request.files["image"]
    xml_file = request.files["xml"]

    if image_file.filename == "" or xml_file.filename == "":
        return "No selected files", 400

    # Ensure upload folder exists
    os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)

    # Save uploaded files
    image_path = os.path.join(
        Config.UPLOAD_FOLDER,
        image_file.filename
    )

    xml_path = os.path.join(
        Config.UPLOAD_FOLDER,
        xml_file.filename
    )

    image_file.save(image_path)
    xml_file.save(xml_path)

    # Extract date from filename
    date_str = os.path.basename(
        image_file.filename
    ).split(".")[0]

    try:
        # Process attendance
        manager = AttendanceManager()

        students_list = manager.parse_students_text(xml_path)
        if not students_list:
            return "Failed to parse XML data.", 400

        thresh_img, step_images = manager.process_image_web(
            image_path
        )

        attendance_results = manager.analyze_attendance_web(
            thresh_img,
            students_list,
            date_str
        )

        return render_template(
            "results.html",
            results=attendance_results,
            steps=step_images,
            date=date_str
        )

    except Exception as e:
        return f"Error processing attendance: {str(e)}", 500


# ==================== Student Management Routes ====================

@attendance_bp.route("/api/students", methods=["GET"])
@require_auth
def get_all_students():
    """Get all students"""
    students = db.get_all_students()
    return jsonify(students), 200


@attendance_bp.route("/api/students/<student_index>", methods=["GET"])
@require_auth
def get_student(student_index):
    """Get specific student"""
    student = db.get_student(student_index)
    
    if student:
        return jsonify(student), 200
    
    return jsonify({"error": "Student not found"}), 404


@attendance_bp.route("/api/students", methods=["POST"])
@require_auth
def create_student():
    """Create new student"""
    data = request.get_json()
    
    if not data or not data.get("student_index") or not data.get("student_name"):
        return jsonify({"error": "Missing required fields"}), 400
    
    if db.add_student(
        data["student_index"],
        data["student_name"],
        data.get("email"),
        data.get("phone")
    ):
        return jsonify({"message": "Student created"}), 201
    
    return jsonify({"error": "Student already exists or creation failed"}), 400


@attendance_bp.route("/api/students/<student_index>", methods=["PUT"])
@require_auth
def update_student(student_index):
    """Update student information"""
    data = request.get_json()
    
    if db.update_student(
        student_index,
        data.get("student_name"),
        data.get("email"),
        data.get("phone")
    ):
        return jsonify({"message": "Student updated"}), 200
    
    return jsonify({"error": "Update failed"}), 400


@attendance_bp.route("/api/students/<student_index>", methods=["DELETE"])
@require_auth
def delete_student(student_index):
    """Delete student"""
    if db.delete_student(student_index):
        return jsonify({"message": "Student deleted"}), 200
    
    return jsonify({"error": "Deletion failed"}), 400


# ==================== Attendance History Routes ====================

@attendance_bp.route("/api/attendance/records", methods=["GET"])
@require_auth
def get_attendance_records():
    """Get attendance records with filtering"""
    date = request.args.get("date")
    student_index = request.args.get("student_index")
    status = request.args.get("status")
    limit = request.args.get("limit", 100, type=int)
    
    records = db.get_attendance_records(
        date=date,
        student_index=student_index,
        status=status,
        limit=limit
    )
    
    return jsonify(records), 200


@attendance_bp.route("/api/attendance/date/<date>", methods=["GET"])
@require_auth
def get_attendance_by_date(date):
    """Get attendance for specific date"""
    records = db.get_attendance_by_date(date)
    return jsonify(records), 200


@attendance_bp.route("/api/attendance/student/<student_index>", methods=["GET"])
@require_auth
def get_student_attendance(student_index):
    """Get student attendance history"""
    days = request.args.get("days", 30, type=int)
    records = db.get_student_attendance(student_index, days=days)
    return jsonify(records), 200


@attendance_bp.route("/api/attendance/<int:attendance_id>", methods=["PUT"])
@require_auth
def update_attendance(attendance_id):
    """Update attendance status"""
    data = request.get_json()
    
    if not data or not data.get("status"):
        return jsonify({"error": "Missing status"}), 400
    
    if db.update_attendance(attendance_id, data["status"]):
        return jsonify({"message": "Attendance updated"}), 200
    
    return jsonify({"error": "Update failed"}), 400


# ==================== Dashboard & Statistics Routes ====================

@attendance_bp.route("/api/dashboard/overview", methods=["GET"])
@require_auth
def get_overview():
    """Get dashboard overview statistics"""
    stats = dashboard_manager.get_overview_stats()
    return jsonify(stats), 200


@attendance_bp.route("/api/dashboard/performance", methods=["GET"])
@require_auth
def get_performance():
    """Get student performance"""
    days = request.args.get("days", 30, type=int)
    performance = dashboard_manager.get_student_performance(days=days)
    return jsonify(performance), 200


@attendance_bp.route("/api/dashboard/daily/<date>", methods=["GET"])
@require_auth
def get_daily_summary(date):
    """Get daily attendance summary"""
    summary = dashboard_manager.get_daily_summary(date)
    return jsonify(summary), 200


@attendance_bp.route("/api/dashboard/trends", methods=["GET"])
@require_auth
def get_trends():
    """Get attendance trends"""
    days = request.args.get("days", 7, type=int)
    trends = dashboard_manager.get_trends(days=days)
    return jsonify(trends), 200


@attendance_bp.route("/api/dashboard/top-performers", methods=["GET"])
@require_auth
def get_top_performers():
    """Get top performing students"""
    limit = request.args.get("limit", 10, type=int)
    days = request.args.get("days", 30, type=int)
    performers = dashboard_manager.get_top_performers(limit=limit, days=days)
    return jsonify(performers), 200


@attendance_bp.route("/api/dashboard/alerts", methods=["GET"])
@require_auth
def get_alerts():
    """Get attendance alerts"""
    threshold = request.args.get("threshold", 75.0, type=float)
    alerts = dashboard_manager.get_attendance_alerts(threshold=threshold)
    return jsonify(alerts), 200


@attendance_bp.route("/api/dashboard/department", methods=["GET"])
@require_auth
def get_department_stats():
    """Get department statistics"""
    stats = dashboard_manager.get_department_stats()
    return jsonify(stats), 200


# ==================== Export Routes ====================

@attendance_bp.route("/api/export/attendance", methods=["GET"])
@require_auth
def export_attendance():
    """Export attendance data"""
    date = request.args.get("date")
    student_index = request.args.get("student_index")
    status = request.args.get("status")
    format = request.args.get("format", "csv")
    
    records = db.get_attendance_records(
        date=date,
        student_index=student_index,
        status=status,
        limit=10000
    )
    
    if not records:
        return jsonify({"error": "No records to export"}), 400
    
    filepath = ExportManager.export_attendance_report(records, format=format)
    
    if filepath and os.path.exists(filepath):
        return send_file(filepath, as_attachment=True)
    
    return jsonify({"error": "Export failed"}), 500


@attendance_bp.route("/api/export/report", methods=["GET"])
@require_auth
def export_report():
    """Export summary report"""
    stats = dashboard_manager.get_overview_stats()
    filepath = ExportManager.generate_summary_report(stats)
    
    if filepath and os.path.exists(filepath):
        return send_file(filepath, as_attachment=True)
    
    return jsonify({"error": "Report generation failed"}), 500


# ==================== Search & Filter Routes ====================

@attendance_bp.route("/api/search/students", methods=["GET"])
@require_auth
def search_students():
    """Search students"""
    query = request.args.get("q", "").lower()
    students = db.get_all_students()
    
    results = [
        s for s in students
        if query in s.get("student_index", "").lower() or 
           query in s.get("student_name", "").lower()
    ]
    
    return jsonify(results), 200


@attendance_bp.route("/api/search/attendance", methods=["GET"])
@require_auth
def search_attendance():
    """Search attendance records"""
    date = request.args.get("date")
    student_index = request.args.get("student_index")
    status = request.args.get("status")
    
    records = db.get_attendance_records(
        date=date,
        student_index=student_index,
        status=status
    )
    
    return jsonify(records), 200
