import os
import uuid
import csv
import io
from flask import (
    Blueprint,
    request,
    jsonify,
    current_app,
    g,
    Response
)

api_bp = Blueprint("api", __name__, url_prefix="/api")

def get_db():
    if "db" not in g:
        from app.models.database import DatabaseManager
        g.db = DatabaseManager(current_app.config["DATABASE"])
    return g.db

def allowed_file(filename, allowed_extensions):
    ext = os.path.splitext(filename)[1].lower()
    return ext in allowed_extensions


@api_bp.route("/upload", methods=["POST"])
def process_upload():
    """Endpoint for uploading attendance image and student information file"""
    if "image" not in request.files or "xml" not in request.files:
        return jsonify({"success": False, "error": "Missing image or student data file."}), 400

    image_file = request.files["image"]
    student_file = request.files["xml"]

    if image_file.filename == "" or student_file.filename == "":
        return jsonify({"success": False, "error": "No file selected."}), 400

    if not allowed_file(image_file.filename, current_app.config["ALLOWED_IMAGE_EXTENSIONS"]):
        return jsonify({"success": False, "error": "Invalid image format. Allowed: PNG, JPG, JPEG, WEBP"}), 400

    if not allowed_file(student_file.filename, current_app.config["ALLOWED_DATA_EXTENSIONS"]):
        return jsonify({"success": False, "error": "Invalid student info format. Allowed: XML, JSON"}), 400

    # Read optional custom CV settings
    signature_ratio = float(request.form.get("signature_ratio", current_app.config["CV_SIGNATURE_START_RATIO"]))
    threshold_val = int(request.form.get("threshold_val", current_app.config["CV_THRESHOLD_VALUE"]))
    pixel_threshold = int(request.form.get("pixel_threshold", current_app.config["CV_PRESENT_PIXEL_THRESHOLD"]))
    use_otsu = request.form.get("use_otsu", "false").lower() == "true"

    session_key = str(uuid.uuid4())[:8]
    upload_folder = current_app.config["UPLOAD_FOLDER"]
    os.makedirs(upload_folder, exist_ok=True)

    img_filename = f"{session_key}_{image_file.filename}"
    img_path = os.path.join(upload_folder, img_filename)
    image_file.save(img_path)

    student_filename = f"{session_key}_{student_file.filename}"
    student_path = os.path.join(upload_folder, student_filename)
    student_file.save(student_path)

    from app.services.cv_engine import CVEngine
    cv_engine = CVEngine(upload_folder, current_app.config)

    students = cv_engine.parse_student_file(student_path)
    if not students:
        return jsonify({"success": False, "error": "Failed to parse student data from uploaded file."}), 400

    date_str = os.path.splitext(image_file.filename)[0]
    title = f"Attendance - {date_str}"

    try:
        step_images, results = cv_engine.process_and_analyze(
            image_path=img_path,
            students=students,
            session_prefix=session_key,
            signature_ratio=signature_ratio,
            threshold_val=threshold_val,
            pixel_threshold=pixel_threshold,
            use_otsu=use_otsu
        )

        db = get_db()
        session_id = db.save_session_results(
            session_key=session_key,
            title=title,
            date_str=date_str,
            step_images=step_images,
            results=results
        )

        return jsonify({
            "success": True,
            "session_id": session_id,
            "session_key": session_key,
            "redirect_url": f"/results/{session_id}"
        })

    except Exception as e:
        return jsonify({"success": False, "error": f"CV Processing Error: {str(e)}"}), 500


@api_bp.route("/records/<int:record_id>/toggle", methods=["POST"])
def toggle_record(record_id):
    """Manually override attendance record status (Present/Absent)"""
    db = get_db()
    updated_info = db.toggle_record_status(record_id)
    if not updated_info:
        return jsonify({"success": False, "error": "Record not found."}), 404

    return jsonify({"success": True, "data": updated_info})


@api_bp.route("/sessions/<int:session_id>/export", methods=["GET"])
def export_session_csv(session_id):
    """Export attendance results for a session as CSV download"""
    db = get_db()
    session = db.get_session(session_id)
    if not session:
        return jsonify({"error": "Session not found"}), 404

    records = db.get_session_records(session_id)

    output = io.StringIO()
    writer = csv.writer(output)

    writer.writerow(["Index", "Student Name", "Status", "Raw Pixel Count", "Manually Overridden"])

    for r in records:
        writer.writerow([
            r["student_index"],
            r["student_name"],
            r["status"],
            r["pixel_count"],
            "Yes" if r["is_manually_overridden"] else "No"
        ])

    csv_data = output.getvalue()

    filename = f"Attendance_{session['date_str']}_{session['session_key']}.csv"
    return Response(
        csv_data,
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@api_bp.route("/analytics/stats", methods=["GET"])
def get_analytics_stats():
    """Retrieve JSON statistics for frontend charts"""
    db = get_db()
    stats = db.get_analytics_summary()
    return jsonify({"success": True, "data": stats})
