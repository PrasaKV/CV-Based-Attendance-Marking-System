import os


class Config:
    """Base configuration"""
    UPLOAD_FOLDER = os.path.join("static", "uploads")
    DATABASE = "attendance.db"
    SECRET_KEY = "your-secret-key-here"


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
    DATABASE = "test_attendance.db"


config = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "testing": TestingConfig,
    "default": DevelopmentConfig
}
