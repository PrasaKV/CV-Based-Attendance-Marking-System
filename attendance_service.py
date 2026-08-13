import cv2

from database import AttendanceDatabase
from roster_parser import RosterParser
from signature_processor import SignatureSheetProcessor


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
