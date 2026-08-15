import os
from flask import Flask, render_template, request

from attendance_core import AttendanceService

UPLOAD_DIR = "static/uploads"

app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = UPLOAD_DIR
os.makedirs(UPLOAD_DIR, exist_ok=True)

service = AttendanceService()

/// save 
def _save_upload(file_storage):
    dest = os.path.join(app.config["UPLOAD_FOLDER"], file_storage.filename)
    file_storage.save(dest)
    return dest


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/upload", methods=["POST"])
def upload_sheet():
    if "image" not in request.files or "xml" not in request.files:
        return "Missing files", 400

    image_file = request.files["image"]
    xml_file = request.files["xml"]

    if image_file.filename == "" or xml_file.filename == "":
        return "No selected files", 400

    image_path = _save_upload(image_file)
    xml_path = _save_upload(xml_file)

    session_date = os.path.splitext(os.path.basename(image_file.filename))[0]

    roster = service.load_roster(xml_path)
    if not roster:
        return "Failed to parse XML data.", 400

    binarized_img, step_previews = service.process_sheet(image_path)
    attendance_records = service.evaluate_attendance(binarized_img, roster, session_date)

    return render_template(
        "results.html",
        results=attendance_records,
        steps=step_previews,
        date=session_date,
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
