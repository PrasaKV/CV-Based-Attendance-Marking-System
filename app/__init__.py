import os

from flask import Flask

from app.config import Config
from app.extensions import db
from app.face_engine import FaceEngine


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    os.makedirs(Config.DATASET_DIR, exist_ok=True)
    os.makedirs(Config.MODEL_DIR, exist_ok=True)
    os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)

    db.init_app(app)
    app.face_engine = FaceEngine(Config)

    from app.blueprints.main.routes import main_bp
    from app.blueprints.students.routes import students_bp
    from app.blueprints.attendance.routes import attendance_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(students_bp, url_prefix="/students")
    app.register_blueprint(attendance_bp, url_prefix="/attendance")

    with app.app_context():
        db.create_all()

    return app
