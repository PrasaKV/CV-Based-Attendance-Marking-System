"""
Legacy compatibility wrapper for services
"""
from app.services.cv_engine import CVEngine
from app.models.database import DatabaseManager

class AttendanceManager:
    """Legacy wrapper for AttendanceManager"""
    def __init__(self, db_name="attendance.db"):
        self.db_manager = DatabaseManager(db_name)
        self.engine = CVEngine("app/static/uploads")

    def parse_students_text(self, xml_file):
        return self.engine.parse_student_file(xml_file)

    def process_image_web(self, image_path):
        steps, _ = self.engine.process_and_analyze(image_path, [{"index": "1", "name": "Dummy"}], "legacy")
        return None, steps

    def analyze_attendance_web(self, thresh_img, students_list, date_str):
        return []
