import os
import re
import xml.etree.ElementTree as ET
import json
import cv2
import numpy as np


class CVEngine:
    """Enhanced Computer Vision Engine for Attendance Detection and Verification"""

    def __init__(self, upload_folder, config=None):
        self.upload_folder = upload_folder
        self.config = config

    def parse_student_file(self, file_path):
        """Parse student index and name from XML or JSON files"""
        students = []
        ext = os.path.splitext(file_path)[1].lower()

        if ext == ".xml":
            students = self._parse_xml(file_path)
        elif ext == ".json":
            students = self._parse_json(file_path)

        return students

    def _parse_xml(self, xml_file):
        students = []
        try:
            tree = ET.parse(xml_file)
            root = tree.getroot()

            # Strategy 1: Iterate student elements
            for student_elem in root.iter("student"):
                idx_elem = student_elem.find("index")
                name_elem = student_elem.find("name")
                if idx_elem is not None and name_elem is not None:
                    students.append({
                        "index": idx_elem.text.strip() if idx_elem.text else "",
                        "name": name_elem.text.strip() if name_elem.text else ""
                    })

            # Strategy 2: Fallback regex if XML schema varies
            if not students:
                with open(xml_file, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()

                indices = re.findall(r"<index[^>]*>([^<]+)</index>", content)
                names = re.findall(r"<name>([^<]+)</name>", content)

                for idx, name in zip(indices, names):
                    students.append({
                        "index": idx.strip(),
                        "name": name.strip()
                    })

        except Exception as e:
            print(f"[CVEngine] XML Parsing error: {e}")
            # Fallback regex parsing on raw text
            try:
                with open(xml_file, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
                indices = re.findall(r"<index[^>]*>([^<]+)</index>", content)
                names = re.findall(r"<name>([^<]+)</name>", content)
                for idx, name in zip(indices, names):
                    students.append({"index": idx.strip(), "name": name.strip()})
            except Exception as inner_e:
                print(f"[CVEngine] Fallback XML parse failed: {inner_e}")

        return students

    def _parse_json(self, json_file):
        students = []
        try:
            with open(json_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            if isinstance(data, list):
                for item in data:
                    students.append({
                        "index": str(item.get("index", "")).strip(),
                        "name": str(item.get("name", "")).strip()
                    })
            elif isinstance(data, dict) and "students" in data:
                for item in data["students"]:
                    students.append({
                        "index": str(item.get("index", "")).strip(),
                        "name": str(item.get("name", "")).strip()
                    })
        except Exception as e:
            print(f"[CVEngine] JSON Parsing error: {e}")

        return students

    def process_and_analyze(
        self,
        image_path,
        students,
        session_prefix,
        signature_ratio=0.60,
        threshold_val=127,
        pixel_threshold=100,
        use_otsu=False
    ):
        """Processes attendance sheet image, performs ROI thresholding, crops signatures, and generates annotated image"""
        img = cv2.imread(image_path)
        if img is None:
            raise ValueError(f"Unable to load image at: {image_path}")

        filename = os.path.basename(image_path)
        height, width, _ = img.shape
        num_students = len(students)

        if num_students == 0:
            raise ValueError("Student list is empty.")

        # 1. Grayscale Conversion
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        # Save Grayscale Image
        gray_filename = f"gray_{session_prefix}_{filename}"
        gray_path = os.path.join(self.upload_folder, gray_filename)
        cv2.imwrite(gray_path, gray)

        # 2. Preprocessing & Binarization
        blur = cv2.medianBlur(gray, 5)

        if use_otsu:
            _, thresh = cv2.threshold(blur, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
        else:
            _, thresh = cv2.threshold(blur, threshold_val, 255, cv2.THRESH_BINARY_INV)

        # Save Thresholded Binarized Image
        thresh_filename = f"thresh_{session_prefix}_{filename}"
        thresh_path = os.path.join(self.upload_folder, thresh_filename)
        cv2.imwrite(thresh_path, thresh)

        # 3. Copy original for drawing visual bounding box overlay
        annotated_img = img.copy()
        row_height = height // num_students

        results = []

        for i, student in enumerate(students):
            y_start = i * row_height
            y_end = (i + 1) * row_height if i < num_students - 1 else height

            x_sig_start = int(width * signature_ratio)
            x_sig_end = width

            # Signature Region of Interest (ROI) in thresholded image
            sig_roi = thresh[y_start:y_end, x_sig_start:x_sig_end]
            non_zero_pixels = int(cv2.countNonZero(sig_roi))

            status = "Present" if non_zero_pixels >= pixel_threshold else "Absent"

            # Crop individual student signature image for visual inspection
            orig_crop = img[y_start:y_end, x_sig_start:x_sig_end]
            safe_index = re.sub(r'[^a-zA-Z0-9]', '_', student['index'])
            crop_filename = f"crop_{session_prefix}_{safe_index}.png"
            crop_path = os.path.join(self.upload_folder, crop_filename)
            cv2.imwrite(crop_path, orig_crop)

            # Draw visual bounding box annotations on annotated image
            color = (46, 204, 113) if status == "Present" else (231, 76, 60) # Green / Red (BGR)
            
            # Row border
            cv2.rectangle(annotated_img, (0, y_start), (width, y_end), (200, 200, 200), 1)

            # Signature ROI border
            cv2.rectangle(annotated_img, (x_sig_start, y_start), (x_sig_end - 2, y_end - 2), color, 2)

            # Draw label box
            label_text = f"{student['index']}: {status} ({non_zero_pixels}px)"
            cv2.putText(
                annotated_img,
                label_text,
                (x_sig_start + 8, y_start + max(20, row_height // 2)),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.55,
                color,
                2,
                cv2.LINE_AA
            )

            results.append({
                "index": student["index"],
                "name": student["name"],
                "status": status,
                "pixel_count": non_zero_pixels,
                "crop_image": f"uploads/{crop_filename}"
            })

        # Save Annotated Image
        annotated_filename = f"annotated_{session_prefix}_{filename}"
        annotated_path = os.path.join(self.upload_folder, annotated_filename)
        cv2.imwrite(annotated_path, annotated_img)

        step_images = {
            "original": f"uploads/{filename}",
            "annotated": f"uploads/{annotated_filename}",
            "grayscale": f"uploads/{gray_filename}",
            "binarized": f"uploads/{thresh_filename}"
        }

        return step_images, results
