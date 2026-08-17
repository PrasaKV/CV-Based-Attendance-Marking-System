import os
import cv2


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
        thresholded = cv2.adaptiveThreshold(
            smoothed, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 21, 10
        )
        return thresholded

    def _save(self, img, filename):
        path = os.path.join(self.OUTPUT_DIR, filename)
        cv2.imwrite(path, img)
        return path
