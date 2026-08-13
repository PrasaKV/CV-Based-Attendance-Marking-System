"""
Legacy compatibility wrapper redirecting to app services
"""
import os
from flask import Blueprint, render_template, request, redirect, url_for
from app.models.database import DatabaseManager
from app.services.cv_engine import CVEngine
from config import Config

attendance_bp = Blueprint("attendance_legacy", __name__)

@attendance_bp.route("/", methods=["GET"])
def index():
    return redirect(url_for("web.index"))

@attendance_bp.route("/upload", methods=["POST"])
def upload():
    if "image" not in request.files or "xml" not in request.files:
        return "Missing files", 400

    image_file = request.files["image"]
    xml_file = request.files["xml"]

    if image_file.filename == "" or xml_file.filename == "":
        return "No selected files", 400

    os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)

    image_path = os.path.join(Config.UPLOAD_FOLDER, image_file.filename)
    xml_path = os.path.join(Config.UPLOAD_FOLDER, xml_file.filename)

    image_file.save(image_path)
    xml_file.save(xml_path)

    date_str = os.path.basename(image_file.filename).split(".")[0]

    cv_engine = CVEngine(Config.UPLOAD_FOLDER)
    students = cv_engine.parse_student_file(xml_path)

    step_images, results = cv_engine.process_and_analyze(
        image_path=image_path,
        students=students,
        session_prefix="legacy"
    )

    db = DatabaseManager(Config.DATABASE)
    session_id = db.save_session_results(
        session_key=date_str,
        title=f"Attendance {date_str}",
        date_str=date_str,
        step_images=step_images,
        results=results
    )

    return redirect(url_for("web.results", session_id_or_key=session_id))
