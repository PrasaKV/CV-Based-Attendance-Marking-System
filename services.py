"""
Legacy compatibility wrapper for services
"""
import cv2
import sqlite3
import os
import re
from config import Config


class AttendanceManager:
    """Manages attendance marking and image processing"""
    
    SIGNATURE_START_RATIO = 0.6
    THRESHOLD_VALUE = 127
    MEDIAN_BLUR_SIZE = 5
    PRESENT_PIXEL_THRESHOLD = 100

    def __init__(self, db_name=None):
        self.db_name = db_name or Config.DATABASE
        self.upload_folder = Config.UPLOAD_FOLDER
        self.init_db()

    def init_db(self):
        """Initialize the database with attendance table"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS attendance (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT,
                student_index TEXT,
                student_name TEXT,
                status TEXT
            )
            """
        )

        conn.commit()
        conn.close()

    def parse_students_text(self, xml_file):
        from roster_parser import RosterParser
        return RosterParser.load(xml_file)

    def process_image_web(self, image_path):
        from signature_processor import SignatureSheetProcessor
        processor = SignatureSheetProcessor()
        binarized, steps = processor.process(image_path)
        return binarized, steps

    def analyze_attendance_web(
        self,
        binarized_img,
        students,
        date
    ):
        """Analyze attendance from processed image"""
        if not students:
            return []

        height, width = binarized_img.shape
        row_height = height // len(students)

        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        results = []

        for i, student in enumerate(students):
            y_start = i * row_height
            y_end = (i + 1) * row_height

            x_start = int(
                width * self.SIGNATURE_START_RATIO
            )
            x_end = width

            signature_roi = binarized_img[
                y_start:y_end,
                x_start:x_end
            ]

            pixel_count = cv2.countNonZero(
                signature_roi
            )

            status = (
                "Present"
                if pixel_count > self.PRESENT_PIXEL_THRESHOLD
                else "Absent"
            )

            results.append(
                {
                    "index": student["index"],
                    "name": student["name"],
                    "status": status
                }
            )

            cursor.execute(
                """
                INSERT INTO attendance
                (date, student_index, student_name, status)
                VALUES (?, ?, ?, ?)
                """,
                (
                    date,
                    student["index"],
                    student["name"],
                    status
                )
            )

        conn.commit()
        conn.close()

        return results
