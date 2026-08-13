from datetime import datetime

from app.extensions import db


class Student(db.Model):
    __tablename__ = "students"

    id = db.Column(db.Integer, primary_key=True)
    roll_no = db.Column(db.String(50), unique=True, nullable=False)
    name = db.Column(db.String(120), nullable=False)
    sample_count = db.Column(db.Integer, default=0, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    attendance_records = db.relationship(
        "AttendanceRecord",
        backref="student",
        cascade="all, delete-orphan",
    )


class AttendanceRecord(db.Model):
    __tablename__ = "attendance_records"

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("students.id"), nullable=False)
    date = db.Column(db.String(10), nullable=False)  # ISO format: YYYY-MM-DD
    status = db.Column(db.String(10), nullable=False)  # "Present" or "Absent"
    confidence = db.Column(db.Float, nullable=True)
    marked_at = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (
        db.UniqueConstraint("student_id", "date", name="uq_student_date"),
    )
