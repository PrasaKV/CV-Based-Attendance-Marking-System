from datetime import date

from flask import Blueprint, render_template

from app.models import AttendanceRecord, Student

main_bp = Blueprint("main", __name__)


@main_bp.route("/")
def dashboard():
    student_count = Student.query.count()
    today = date.today().isoformat()
    today_records = AttendanceRecord.query.filter_by(date=today).all()
    present_today = sum(1 for r in today_records if r.status == "Present")

    return render_template(
        "dashboard.html",
        student_count=student_count,
        today=today,
        present_today=present_today,
        marked_today=len(today_records),
    )
