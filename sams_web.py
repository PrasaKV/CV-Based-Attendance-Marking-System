import cv2
import numpy as np
import sqlite3
import os
import re

class AttendanceManager:
    def __init__(self, db_name="attendance.db"):
        self.db_name = db_name
        self.init_db()

    def init_db(self):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS attendance (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT,
                student_index TEXT,
                student_name TEXT,
                status TEXT
            )
        ''')
        conn.commit()
        conn.close()

    def parse_students_text(self, xml_file):
        students = []
        try:
            with open(xml_file, 'r') as f:
                content = f.read()
            indices = re.findall(r'<index[^>]*>([^<]+)</index>', content)
            names = re.findall(r'<name>([^<]+)</name>', content)
            for idx, name in zip(indices, names):
                students.append({'index': idx.strip(), 'name': name.strip()})
            return students
        except Exception as e:
            print(f"Error reading info file: {e}")
            return students

    def process_image_web(self, image_path):
        img = cv2.imread(image_path)
        filename = os.path.basename(image_path)
        
        # 1. Grayscale
        gray_img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        gray_path = f"static/uploads/gray_{filename}"
        cv2.imwrite(gray_path, gray_img)
        
        # 2. Blur & Binarize
        blur = cv2.medianBlur(gray_img, 5)
        ret, thresh_img = cv2.threshold(blur, 127, 255, cv2.THRESH_BINARY_INV)
        thresh_path = f"static/uploads/thresh_{filename}"
        cv2.imwrite(thresh_path, thresh_img)
        
        step_images = {
            'original': f"uploads/{filename}",
            'grayscale': f"uploads/gray_{filename}",
            'binarized': f"uploads/thresh_{filename}"
        }
        
        return thresh_img, step_images

    def analyze_attendance_web(self, binarized_img, students, date):
        height, width = binarized_img.shape
        row_height = height // len(students)
        
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        results = []

        for i, student in enumerate(students):
            y_start = i * row_height
            y_end = (i + 1) * row_height
            x_start = int(width * 0.6) 
            x_end = width
            
            signature_roi = binarized_img[y_start:y_end, x_start:x_end]
            pixel_count = cv2.countNonZero(signature_roi)
            status = "Present" if pixel_count > 100 else "Absent"
            
            results.append({
                'index': student['index'],
                'name': student['name'],
                'status': status
            })
            
            cursor.execute('''
                INSERT INTO attendance (date, student_index, student_name, status)
                VALUES (?, ?, ?, ?)
            ''', (date, student['index'], student['name'], status))
            
        conn.commit()
        conn.close()
        return results