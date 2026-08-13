import os

from flask import Flask, render_template, request
from sams_web import AttendanceManager


app = Flask(__name__)

UPLOAD_FOLDER = "static/uploads"

ALLOWED_IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg"}
ALLOWED_XML_EXTENSIONS = {".xml"}

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

os.makedirs(
    app.config["UPLOAD_FOLDER"],
    exist_ok=True
)


def is_allowed_file(filename, allowed_extensions):
    extension = os.path.splitext(filename)[1].lower()
    return extension in allowed_extensions


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/upload", methods=["POST"])
def upload():
    if "image" not in request.files or "xml" not in request.files:
        return "Missing files. Please upload both an image and an XML file.", 400

    image_file = request.files["image"]
    xml_file = request.files["xml"]

    if image_file.filename == "" or xml_file.filename == "":
        return "No selected files. Please choose both files.", 400

    if not is_allowed_file(
        image_file.filename,
        ALLOWED_IMAGE_EXTENSIONS
    ):
        return "Invalid image format. Please upload a PNG or JPG image.", 400

    if not is_allowed_file(
        xml_file.filename,
        ALLOWED_XML_EXTENSIONS
    ):
        return "Invalid XML file. Please upload an XML file.", 400

    image_path = os.path.join(
        app.config["UPLOAD_FOLDER"],
        image_file.filename
    )

    xml_path = os.path.join(
        app.config["UPLOAD_FOLDER"],
        xml_file.filename
    )

    image_file.save(image_path)
    xml_file.save(xml_path)

    date_str = os.path.basename(
        image_file.filename
    ).split(".")[0]

    manager = AttendanceManager()

    students_list = manager.parse_students_text(
        xml_path
    )

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


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )