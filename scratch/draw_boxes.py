import cv2
import numpy as np

img = cv2.imread(r"c:\Users\94781\Documents\GitHub\CV-Based-Attendance-Marking-System\static\uploads\thresh_3.jpeg")
height, width = img.shape[:2]

# Draw x_start and x_end lines
x1 = int(width * 0.6)
x2 = width
cv2.line(img, (x1, 0), (x1, height), (0, 0, 255), 5) # Red for 0.6

x3 = int(width * 0.75)
x4 = int(width * 0.95)
cv2.line(img, (x3, 0), (x3, height), (0, 255, 0), 5) # Green for 0.75
cv2.line(img, (x4, 0), (x4, height), (0, 255, 0), 5)

cv2.imwrite(r"c:\Users\94781\Documents\GitHub\CV-Based-Attendance-Marking-System\scratch\debug_lines.jpeg", img)
