import os

APP_DIR = os.path.abspath(os.path.dirname(__file__))
BASE_DIR = os.path.abspath(os.path.join(APP_DIR, os.pardir))


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key")
    SQLALCHEMY_DATABASE_URI = "sqlite:///" + os.path.join(BASE_DIR, "attendance.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    DATA_DIR = os.path.join(BASE_DIR, "data")
    DATASET_DIR = os.path.join(DATA_DIR, "dataset")
    MODEL_DIR = os.path.join(DATA_DIR, "trained_model")
    MODEL_PATH = os.path.join(MODEL_DIR, "lbph_model.yml")

    # Inside app/static so Flask's default static route can serve captures.
    UPLOAD_FOLDER = os.path.join(APP_DIR, "static", "captures")

    FACE_SAMPLE_SIZE = (200, 200)
    MIN_SAMPLES_RECOMMENDED = 5

    # LBPH confidence is a distance score - lower means a closer match.
    RECOGNITION_CONFIDENCE_THRESHOLD = 70
