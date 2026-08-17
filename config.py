import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

class Config:
    """Base configuration"""
    SECRET_KEY = os.environ.get("SECRET_KEY", "sams-secret-key-super-secure-2026")
    UPLOAD_FOLDER = os.path.join(BASE_DIR, "static", "uploads")
    DATABASE = os.path.join(BASE_DIR, "attendance.db")
    
    # Computer Vision Engine Defaults
    CV_SIGNATURE_START_RATIO = 0.60
    CV_THRESHOLD_VALUE = 1276
    CV_MEDIAN_BLUR_SIZE = 5
    CV_PRESENT_PIXEL_THRESHOLD = 100
    CV_USE_OTSU = False

    ALLOWED_IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp"}
    ALLOWED_DATA_EXTENSIONS = {".xml", ".json"}


class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    TESTING = False


class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    TESTING = False


class TestingConfig(Config):
    """Testing configuration"""
    DEBUG = True
    TESTING = True
    DATABASE = os.path.join(BASE_DIR, "test_attendance.db")


config = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "testing": TestingConfig,
    "default": DevelopmentConfig
}
