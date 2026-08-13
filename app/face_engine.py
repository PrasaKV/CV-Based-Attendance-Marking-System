import os

import cv2
import numpy as np


class FaceEngine:
    """Wraps Haar cascade face detection and LBPH face recognition.

    Student primary keys double as LBPH labels, so no separate label
    mapping needs to be persisted alongside the trained model.
    """

    def __init__(self, config):
        self.config = config
        cascade_path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
        self.detector = cv2.CascadeClassifier(cascade_path)
        self.recognizer = cv2.face.LBPHFaceRecognizer_create()
        self._model_loaded = False

    def detect_faces(self, gray_img):
        return self.detector.detectMultiScale(
            gray_img, scaleFactor=1.1, minNeighbors=5, minSize=(60, 60)
        )

    def largest_face(self, gray_img):
        faces = self.detect_faces(gray_img)
        if len(faces) == 0:
            return None
        return max(faces, key=lambda box: box[2] * box[3])

    def crop_face(self, gray_img, box):
        x, y, w, h = box
        face = gray_img[y:y + h, x:x + w]
        return cv2.resize(face, self.config.FACE_SAMPLE_SIZE)

    def save_sample(self, student_id, gray_img):
        box = self.largest_face(gray_img)
        if box is None:
            return False

        face = self.crop_face(gray_img, box)
        student_dir = os.path.join(self.config.DATASET_DIR, str(student_id))
        os.makedirs(student_dir, exist_ok=True)

        existing = len(os.listdir(student_dir))
        sample_path = os.path.join(student_dir, f"{existing + 1}.jpg")
        cv2.imwrite(sample_path, face)
        return True

    def train(self):
        faces = []
        labels = []

        if os.path.isdir(self.config.DATASET_DIR):
            for student_id in os.listdir(self.config.DATASET_DIR):
                student_dir = os.path.join(self.config.DATASET_DIR, student_id)
                if not os.path.isdir(student_dir):
                    continue

                for filename in os.listdir(student_dir):
                    img = cv2.imread(
                        os.path.join(student_dir, filename), cv2.IMREAD_GRAYSCALE
                    )
                    if img is None:
                        continue
                    faces.append(img)
                    labels.append(int(student_id))

        if not faces:
            raise ValueError("No face samples found. Capture samples before training.")

        os.makedirs(self.config.MODEL_DIR, exist_ok=True)
        self.recognizer.train(faces, np.array(labels))
        self.recognizer.save(self.config.MODEL_PATH)
        self._model_loaded = True

        return len(faces), len(set(labels))

    def load_model(self):
        if not os.path.exists(self.config.MODEL_PATH):
            return False
        self.recognizer.read(self.config.MODEL_PATH)
        self._model_loaded = True
        return True

    def recognize(self, gray_img):
        """Detect every face in the image and predict a label for each.

        Returns a list of {box, student_id, confidence} dicts. student_id is
        None when the best match is farther than RECOGNITION_CONFIDENCE_THRESHOLD.
        """
        if not self._model_loaded and not self.load_model():
            raise ValueError("No trained model found. Train the recognizer first.")

        results = []
        for box in self.detect_faces(gray_img):
            face = self.crop_face(gray_img, box)
            label, confidence = self.recognizer.predict(face)

            student_id = None
            if confidence <= self.config.RECOGNITION_CONFIDENCE_THRESHOLD:
                student_id = label

            results.append({"box": box, "student_id": student_id, "confidence": confidence})

        return results
