"""
Service layer for attendance management
"""
import cv2
import os
import re
from config import Config
from database import Database


class AttendanceManager:
    """Manages attendance marking and image processing"""
    
    SIGNATURE_START_RATIO = 0.6
    THRESHOLD_VALUE = 127
    MEDIAN_BLUR_SIZE = 5
    PRESENT_PIXEL_THRESHOLD = 100

    def __init__(self, db_name=None):
        self.db_name = db_name or Config.DATABASE
        self.upload_folder = Config.UPLOAD_FOLDER
        self.db = Database(self.db_name)

    def parse_students_text(self, xml_file):
        """Parse student information from XML file"""
        students = []

        try:
            with open(xml_file, "r") as f:
                content = f.read()

            indices = re.findall(
                r"<index[^>]*>([^<]+)</index>",
                content
            )

            names = re.findall(
                r"<name>([^<]+)</name>",
                content
            )

            for idx, name in zip(indices, names):
                students.append(
                    {
                        "index": idx.strip(),
                        "name": name.strip()
                    }
                )

            return students

        except Exception as e:
            print(f"Error reading info file: {e}")
            return students

    def process_image_web(self, image_path):
        """Process uploaded image for attendance marking"""
        img = cv2.imread(image_path)

        if img is None:
            raise ValueError("Unable to read the uploaded image.")

        filename = os.path.basename(image_path)

        # 1. Convert image to grayscale
        gray_img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        gray_path = os.path.join(
            self.upload_folder,
            f"gray_{filename}"
        )

        cv2.imwrite(gray_path, gray_img)

        # 2. Blur and binarize the image
        blur = cv2.medianBlur(
            gray_img,
            self.MEDIAN_BLUR_SIZE
        )

        _, thresh_img = cv2.threshold(
            blur,
            self.THRESHOLD_VALUE,
            255,
            cv2.THRESH_BINARY_INV
        )

        thresh_path = os.path.join(
            self.upload_folder,
            f"thresh_{filename}"
        )

        cv2.imwrite(thresh_path, thresh_img)

        step_images = {
            "original": f"uploads/{filename}",
            "grayscale": f"uploads/gray_{filename}",
            "binarized": f"uploads/thresh_{filename}"
        }

        return thresh_img, step_images

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

            self.db.insert_attendance(
                date,
                student["index"],
                student["name"],
                status
            