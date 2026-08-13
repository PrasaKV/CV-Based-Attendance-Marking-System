"""
Application entry point
"""
import os
from flask import Flask
from routes import attendance_bp
from config import config


def create_app(config_name="development"):
    """Application factory"""
    app = Flask(__name__)
    
    # Load configuration
    app.config.from_object(config[config_name])
    
    # Ensure upload folder exists
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
    
    # Register blueprints
    app.register_blueprint(attendance_bp)
    
    # Error handlers
    @app.errorhandler(404)
    def not_found(error):
        return {"error": "Resource not found"}, 404
    
    @app.errorhandler(500)
    def server_error(error):
        return {"error": "Internal server error"}, 500
    
    return app


if __name__ == "__main__":
    app = create_app(os.getenv("FLASK_ENV", "development"))
    app.run(
        host="0.0.0.0",
        port=5000,
        debug=app.config["DEBUG"]
    )
