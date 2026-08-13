import os
from flask import Flask
from config import config

def create_app(config_name="development"):
    """Application factory for SAMS"""
    app = Flask(__name__)
    
    # Load configuration
    if isinstance(config_name, str):
        app.config.from_object(config[config_name])
    else:
        app.config.from_object(config_name)

    # Ensure upload directory exists
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

    # Initialize Database Schema
    from app.models.database import DatabaseManager
    DatabaseManager(app.config["DATABASE"])

    # Register Blueprints
    from app.routes.web import web_bp
    from app.routes.api import api_bp

    app.register_blueprint(web_bp)
    app.register_blueprint(api_bp)

    # Legacy blueprint compatibility wrapper
    from routes import attendance_bp
    app.register_blueprint(attendance_bp, url_prefix="/legacy")

    return app
