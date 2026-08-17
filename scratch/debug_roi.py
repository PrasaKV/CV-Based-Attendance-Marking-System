import cv2
import sqlite3
import numpy as np

# Simulate analyze_attendance_web
binarized_img = cv2.imread(r"c:\Users\94781\Documents\GitHub\CV-Based-Attendance-Marking-System\static\uploads\thresh_3.jpeg", cv2.IMREAD_GRAYSCALE)

height, width = binarized_img.shape

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

num_students = 6
print(f"filtered_y: {filtered_y}")
if len(filtered_y) >= num_students + 1:
    row_boundaries = filtered_y[-(num_students + 1):]
else:
    # Fallback to naive splitting
    row_boundaries = [i * (height // num_students) for i in range(num_students + 1)]

print(f"row_boundaries: {row_boundaries}")

for i in range(num_students):
    y_start = row_boundaries[i]
    y_end = row_boundaries[i + 1]

    # Current settings
    x_start = int(width * 0.6)
    x_end = width
    
    margin_y = 10
    margin_x = 10
    safe_y_start = min(y_start + margin_y, y_end)
    safe_y_end = max(y_end - margin_y, y_start)
    safe_x_start = min(x_start + margin_x, x_end)
    safe_x_end = max(x_end - margin_x, x_start)

    # New settings
    x_start_new = int(width * 0.68)
    x_end_new = int(width * 0.80)
    margin_y_new = 10
    margin_x_new = 0
    safe_y_start_new = min(y_start + margin_y_new, y_end)
    safe_y_end_new = max(y_end - margin_y_new, y_start)
    safe_x_start_new = min(x_start_new + margin_x_new, x_end_new)
    safe_x_end_new = max(x_end_new - margin_x_new, x_start_new)
    
    roi_new = binarized_img[safe_y_start_new:safe_y_end_new, safe_x_start_new:safe_x_end_new]
    pixel_count_new = cv2.countNonZero(roi_new)
    cv2.imwrite(rf"c:\Users\94781\Documents\GitHub\CV-Based-Attendance-Marking-System\scratch\roi_new_{i}.png", roi_new)
    print(f"Student {i} (New config): pixel_count = {pixel_count_new}")
