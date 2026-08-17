"""
Legacy compatibility wrapper for services
"""
import cv2
import sqlite3
import os
import re
import numpy as np
from config import Config


class AttendanceManager:
    """Manages attendance marking and image processing"""
    
    SIGNATURE_START_RATIO = 0.68
    THRESHOLD_VALUE = 127
    MEDIAN_BLUR_SIZE = 5
    PRESENT_PIXEL_THRESHOLD = 1000

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
        
        # Detect horizontal lines
        kernel_len = width // 100
        horiz_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (kernel_len, 1))
        
        image_horizontal = cv2.erode(binarized_img, horiz_kernel, iterations=3)
        horizontal_lines = cv2.dilate(image_horizontal, horiz_kernel, iterations=3)
        
        contours, _ = cv2.findContours(horizontal_lines, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        y_coords = []
        for c in contours:
            x, y, w, h = cv2.boundingRect(c)
            if w > width * 0.3:
                y_coords.append(y)
                
        y_coords = sorted(list(set(y_coords)))
        
        filtered_y = []
        for y in y_coords:
            if not filtered_y or y - filtered_y[-1] > 10:
                filtered_y.append(y)
                
        num_students = len(students)
        if len(filtered_y) >= num_students + 1:
            row_boundaries = filtered_y[-(num_students + 1):]
        else:
            # Fallback to naive splitting
            row_boundaries = [i * (height // num_students) for i in range(num_students + 1)]

        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        results = []

        for i, student in enumerate(students):
            y_start = row_boundaries[i]
            y_end = row_boundaries[i + 1]

            x_start = int(
                width * self.SIGNATURE_START_RATIO
            )
            x_end = int(width * 0.82)
            
            # Shrink ROI to avoid table borders being counted as present pixels
            margin_y = 10
            margin_x = 10
            safe_y_start = min(y_start + margin_y, y_end)
            safe_y_end = max(y_end - margin_y, y_start)
            safe_x_start = min(x_start + margin_x, x_end)
            safe_x_end = max(x_end - margin_x, x_start)

            signature_roi = binarized_img[
                safe_y_start:safe_y_end,
                safe_x_start:safe_x_end
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
