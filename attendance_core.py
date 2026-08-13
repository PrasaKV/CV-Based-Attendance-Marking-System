import os
import re
import sqlite3

import cv2


class RosterParser:
    """Extracts student index/name pairs from a simple pseudo-XML roster file."""

    INDEX_PATTERN = re.compile(r"<index[^>]*>([^<]+)</index>")
    NAME_PATTERN = re.compile(r"<name>([^<]+)</name>")

    @classmethod
    def load(cls, path):
        try:
            with open(path, "r") as f:
                content = f.read()
        except OSError as e:
            print(f"Could not read roster file: {e}")
            return []

        indices = cls.INDEX_PATTERN.findall(content)
        names = cls.NAME_PATTERN.findall(content)

        return [
            {"index": idx.strip(), "name": name.strip()}
            for idx, name in zip(indices, names)
        ]


class SignatureSheetProcessor:
    """Converts a scanned signature sheet into a binarized image ready for
    row-by-row analysis, saving intermediate steps for display in the UI.
    """

    OUTPUT_DIR = "static/uploads"

    def __init__(self, blur_kernel=5, threshold=127):
        self.blur_kernel = blur_kernel
        self.threshold = threshold

    def process(self, image_path):
        img = cv2.imread(image_path)
        filename = os.path.basename(image_path)

        grayscale = self._to_grayscale(img)
        self._save(grayscale, f"gray_{filename}")

        binarized = self._binarize(grayscale)
        self._save(binarized, f"thresh_{filename}")

        step_previews = {
            "original": f"uploads/{filename}",
            "grayscale": f"uploads/gray_{filename}",
            "binarized": f"uploads/thresh_{filename}",
        }

        return binarized, step_previews

    def _to_grayscale(self, img):
        return cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    def _binarize(self, gray_img):
        smoothed = cv2.medianBlur(gray_img, self.blur_kernel)
        _, thresholded = cv2.threshold(
            smoothed, self.threshold, 255, cv2.THRESH_BINARY_INV
        )
        return thresholded

    def _save(self, img, filename):
        path = os.path.join(self.OUTPUT_DIR, filename)
        cv2.imwrite(path, img)
        return path


class AttendanceDatabase:
    """Handles persistence of attendance records to SQLite."""

    def __init__(self, db_path="attendance.db"):
        self.db_path = db_path
        self._ensure_schema()

    def _connect(self):
        return sqlite3.connect(self.db_path)

    def _ensure_schema(self):
        with self._connect() as conn:
            conn.execute(
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

    def record_batch(self, date, entries):
        """entries: iterable of dicts with keys 'index', 'name', 'status'."""
        with self._connect() as conn:
            conn.executemany(
                """
                INSERT INTO attendance (date, student_index, student_name, status)
                VALUES (?, ?, ?, ?)
                """,
                [(date, e["index"], e["name"], e["status"]) for e in entries],
            )


class AttendanceService:
    """High-level orchestration: parse the roster, process the scanned sheet,
    detect signatures row by row, and persist the resulting records.
    """

    SIGNATURE_ZONE_START = 0.6  # fraction of image width where the signature column begins
    PRESENCE_PIXEL_THRESHOLD = 100

    def __init__(self, db_name="attendance.db"):
        self.db = AttendanceDatabase(db_name)
        self.image_processor = SignatureSheetProcessor()

    def load_roster(self, xml_path):
        return RosterParser.load(xml_path)

    def process_sheet(self, image_path):
        return self.image_processor.process(image_path)

    def evaluate_attendance(self, binarized_img, roster, date):
        height, width = binarized_img.shape
        row_height = height // len(roster)
        x_start = int(width * self.SIGNATURE_ZONE_START)

        records = [
            {
                "index": student["index"],
                "name": student["name"],
                "status": self._check_row(binarized_img, i, row_height, x_start, width),
            }
            for i, student in enumerate(roster)
        ]

        self.db.record_batch(date, records)
        return records

    def _check_row(self, img, row_index, row_height, x_start, x_end):
        y_start = row_index * row_height
        y_end = y_start + row_height
        roi = img[y_start:y_end, x_start:x_end]
        pixel_count = cv2.countNonZero(roi)
        return "Present" if pixel_count > self.PRESENCE_PIXEL_THRESHOLD else "Absent"
