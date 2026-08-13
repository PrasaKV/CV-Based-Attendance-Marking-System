import base64
import os

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
from app.models import Student

students_bp = Blueprint("students", __name__)


def _decode_upload_image(file_storage):
    data = file_storage.read()
    arr = np.frombuffer(data, dtype=np.uint8)
    return cv2.imdecode(arr, cv2.IMREAD_GRAYSCALE)


def _decode_data_url(data_url):
    _, encoded = data_url.split(",", 1)
    data = base64.b64decode(encoded)
    arr = np.frombuffer(data, dtype=np.uint8)
    return cv2.imdecode(arr, cv2.IMREAD_GRAYSCALE)


@students_bp.route("/")
def list_students():
    students = Student.query.order_by(Student.roll_no).all()
    model_exists = os.path.exists(current_app.config["MODEL_PATH"])
    return render_template(
        "students/list.html", students=students, model_exists=model_exists
    )


@students_bp.route("/add", methods=["GET", "POST"])
def add_student():
    if request.method == "POST":
        roll_no = request.form.get("roll_no", "").strip()
        name = request.form.get("name", "").strip()

        if not roll_no or not name:
            flash("Roll number and name are required.", "error")
            return redirect(url_for("students.add_student"))

        if Student.query.filter_by(roll_no=roll_no).first():
            flash(f"A student with roll number {roll_no} already exists.", "error")
            return redirect(url_for("students.add_student"))

        student = Student(roll_no=roll_no, name=name)
        db.session.add(student)
        db.session.commit()

        return redirect(url_for("students.capture", student_id=student.id))

    return render_template("students/add.html")


@students_bp.route("/<int:student_id>/capture", methods=["GET"])
def capture(student_id):
    student = Student.query.get_or_404(student_id)
    return render_template("students/capture.html", student=student)


@students_bp.route("/<int:student_id>/capture", methods=["POST"])
def capture_submit(student_id):
    student = Student.query.get_or_404(student_id)
    engine = current_app.face_engine

    gray = None
    if request.is_json:
        payload = request.get_json(silent=True) or {}
        image_data = payload.get("image")
        if image_data:
            gray = _decode_data_url(image_data)
    elif "image" in request.files and request.files["image"].filename:
        gray = _decode_upload_image(request.files["image"])

    if gray is None:
        if request.is_json:
            return {"ok": False, "error": "No image received."}, 400
        flash("No image received.", "error")
        return redirect(url_for("students.capture", student_id=student.id))

    saved = engine.save_sample(student.id, gray)
    if not saved:
        if request.is_json:
            return {"ok": False, "error": "No face detected in the image."}, 422
        flash("No face detected in the uploaded photo.", "error")
        return redirect(url_for("students.capture", student_id=student.id))

    student.sample_count += 1
    db.session.commit()

    if request.is_json:
        return {"ok": True, "sample_count": student.sample_count}

    flash("Sample saved.", "success")
    return redirect(url_for("students.capture", student_id=student.id))


@students_bp.route("/train", methods=["POST"])
def train():
    engine = current_app.face_engine

    try:
        sample_total, student_total = engine.train()
    except ValueError as exc:
        flash(str(exc), "error")
        return redirect(url_for("students.list_students"))

    flash(
        f"Trained recognizer on {sample_total} samples across {student_total} student(s).",
        "success",
    )
    return redirect(url_for("students.list_students"))


@students_bp.route("/<int:student_id>/delete", methods=["POST"])
def delete_student(student_id):
    student = Student.query.get_or_404(student_id)

    dataset_dir = os.path.join(current_app.config["DATASET_DIR"], str(student.id))
    if os.path.isdir(dataset_dir):
        for filename in os.listdir(dataset_dir):
            os.remove(os.path.join(dataset_dir, filename))
        os.rmdir(dataset_dir)

    name = student.name
    db.session.delete(student)
    db.session.commit()

    flash(f"Removed {name}. Retrain the recognizer to apply the change.", "success")
    return redirect(url_for("students.list_students"))
