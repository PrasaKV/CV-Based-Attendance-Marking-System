import os
from flask import Flask, render_template, request, redirect, url_for
from sams_web import AttendanceManager

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'static/uploads'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload():
    if 'image' not in request.files or 'xml' not in request.files:
        return "Missing files", 400
    
    image_file = request.files['image']
    xml_file = request.files['xml']
    
    if image_file.filename == '' or xml_file.filename == '':
        return "No selected files", 400

    image_path = os.path.join(app.config['UPLOAD_FOLDER'], image_file.filename)
    xml_path = os.path.join(app.config['UPLOAD_FOLDER'], xml_file.filename)
    
    image_file.save(image_path)
    xml_file.save(xml_path)

    date_str = os.path.basename(image_file.filename).split('.')[0]
    
    manager = AttendanceManager()
    students_list = manager.parse_students_text(xml_path)
    
    if not students_list:
        return "Failed to parse XML data.", 400

    # Process image and get the paths to the intermediate images
    thresh_img, step_images = manager.process_image_web(image_path)
    
    # Get attendance data list to pass to the HTML table
    attendance_results = manager.analyze_attendance_web(thresh_img, students_list, date_str)

    return render_template('results.html', results=attendance_results, steps=step_images, date=date_str)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)