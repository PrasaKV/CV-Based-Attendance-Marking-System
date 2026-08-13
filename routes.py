"""
Routes for the attendance marking system
"""
import os
from flask import Blueprint, render_template, request
from services import AttendanceManager
from config import Config

# Create blueprint
attendance_bp = Blueprint(
    "attendance",
    __name__,
    url_prefix="/"
)


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
