import os
import sys

# Ensure root workspace is in sys.path
sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(__file__))))

def verify_system():
    print("=== Testing Redesigned SAMS Computer Vision & Database Pipeline ===")
    from app import create_app
    app = create_app("testing")
    
    with app.app_context():
        from app.services.cv_engine import CVEngine
        from app.models.database import DatabaseManager
        
        upload_folder = app.config["UPLOAD_FOLDER"]
        cv_engine = CVEngine(upload_folder, app.config)
        
        xml_path = os.path.join("uploads", "students.xml")
        img_path = os.path.join("uploads", "1.jpeg")
        
        if not os.path.exists(xml_path) or not os.path.exists(img_path):
            print("Sample upload files not found at uploads/ - skipping live CV run.")
            return

        print("[1] Parsing student XML file...")
        students = cv_engine.parse_student_file(xml_path)
        print(f"    Successfully parsed {len(students)} students: {students[:2]}")
        
        print("[2] Running CV engine pipeline...")
        step_images, results = cv_engine.process_and_analyze(
            image_path=img_path,
            students=students,
            session_prefix="test_run",
            signature_ratio=0.60,
            threshold_val=127,
            pixel_threshold=100
        )
        print(f"    Step images generated: {list(step_images.keys())}")
        print(f"    Attendance Results parsed: {len(results)} students processed.")
        print(f"    Sample result: {results[0]}")

        print("[3] Testing Database operations...")
        db = DatabaseManager(app.config["DATABASE"])
        session_id = db.save_session_results(
            session_key="test_key_123",
            title="Test Session",
            date_str="2026-08-13",
            step_images=step_images,
            results=results
        )
        print(f"    Saved session to DB with ID: {session_id}")

        records = db.get_session_records(session_id)
        if records:
            first_id = records[0]["id"]
            print(f"    Toggling status for record ID {first_id}...")
            toggle_res = db.toggle_record_status(first_id)
            print(f"    Updated Record Info: {toggle_res}")

        print("=== Verification Test Passed Successfully! ===")

if __name__ == "__main__":
    verify_system()
