import base64
import os
from datetime import date

import cv2
import numpy as np
from flask import (
    Blueprint,
    current_app,
    flash,
    redirect,
    render_template,
    request,
    url_for,
)

from app.extensions import db
from app.models import AttendanceRecord, Student

attendance_bp = Blueprint("attendance", __name__)


def _decode_upload_image_color(file_storage):
    data = file_storage.read()
    arr = np.frombuffer(data, dtype=np.uint8)
    return cv2.imdecode(arr, cv2.IMREAD_COLOR)


def _decode_data_url_color(data_url):
    _, encoded = data_url.split(",", 1)
    data = base64.b64decode(encoded)
    arr = np.frombuffer(data, dtype=np.uint8)
    return cv2.imdecode(arr, cv2.IMREAD_COLOR)


@attendance_bp.route("/take", methods=["GET"])
def take():
    return render_template("attendance/take.html", today=date.today().isoformat())


@attendance_bp.route("/take", methods=["POST"])
def take_submit():
    engine = current_app.face_engine
    session_date = request.form.get("date") or date.today().isoformat()

    image = None
    if "image" in request.files and request.files["image"].filename:
        image = _decode_upload_image_color(request.files["image"])
    else:
        image_data = request.form.get("captured_image")
        if image_data:
            image = _decode_data_url_color(image_data)

    if image is None:
        flash("Please upload or capture a photo.", "error")
        return redirect(url_for("attendance.take"))

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    try:
        detections = engine.recognize(gray)
    except ValueError as exc:
        flash(str(exc), "error")
        return redirect(url_for("attendance.take"))

    # Keep only the closest (lowest-confidence) match per recognized student.
    best_by_student = {}
    unknown_boxes = []
    for det in detections:
        if det["student_id"] is None:
            unknown_boxes.append(det["box"])
            continue

        sid = det["student_id"]
        if sid not in best_by_student or det["confidence"] < best_by_student[sid]["confidence"]:
            best_by_student[sid] = det

    students = Student.query.all()
    student_by_id = {s.id: s for s in students}

    results = []
    for student in students:
        match = best_by_student.get(student.id)
        status = "Present" if match else "Absent"
        confidence = match["confidence"] if match else None

        record = AttendanceRecord.query.filter_by(
            student_id=student.id, date=session_date
        ).first()

        if record:
            record.status = status
            record.confidence = confidence
        else:
            record = AttendanceRecord(
                student_id=student.id,
                date=session_date,
                status=status,
                confidence=confidence,
            )
            db.session.add(record)

        results.append(
            {
                "roll_no": student.roll_no,
                "name": student.name,
                "status": status,
                "confidence": round(confidence, 1) if confidence is not None else None,
            }
        )

    db.session.commit()
    results.sort(key=lambda r: r["roll_no"])

    image_filename = _annotate_and_save(
        image, session_date, unknown_boxes, student_by_id, best_by_student
    )

    return render_template(
        "attendance/results.html",
        results=results,
        date=session_date,
        image_path=image_filename,
        unknown_count=len(unknown_boxes),
    )


def _annotate_and_save(image, session_date, unknown_boxes, student_by_id, best_by_student):
    annotated = image.copy()

    for sid, det in best_by_student.items():
        x, y, w, h = det["box"]
        name = student_by_id[sid].name
        cv2.rectangle(annotated, (x, y), (x + w, y + h), (0, 170, 0), 2)
        cv2.putText(
            annotated, name, (x, max(y - 10, 0)),
            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 170, 0), 2,
        )

    for (x, y, w, h) in unknown_boxes:
        cv2.rectangle(annotated, (x, y), (x + w, y + h), (0, 0, 200), 2)
        cv2.putText(
            annotated, "Unknown", (x, max(y - 10, 0)),
            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 200), 2,
        )

    filename = f"attendance_{session_date}.jpg"
    path = os.path.join(current_app.config["UPLOAD_FOLDER"], filename)
    cv2.imwrite(path, annotated)
    return filename


@attendance_bp.route("/history")
def history():
    rows = (
        db.session.query(AttendanceRecord.date)
        .distinct()
        .order_by(AttendanceRecord.date.desc())
        .all()
    )

    dates = []
    for (session_date,) in rows:
        records = AttendanceRecord.query.filter_by(date=session_date).all()
        present = sum(1 for r in records if r.status == "Present")
        dates.append({"date": session_date, "present": present, "total": len(records)})

    return render_template("attendance/history.html", dates=dates)


@attendance_bp.route("/history/<date_str>")
def history_detail(date_str):
    records = (
        AttendanceRecord.query.filter_by(date=date_str)
        .join(Student)
        .order_by(Student.roll_no)
        .all()
    )
    return render_template("attendance/history_detail.html", date=date_str, records=records)
