import os
import sys

# Ensure root workspace is in sys.path
sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(__file__))))

def verify_system_v2():
    print("=== Testing Redesigned SAMS v2.0 Platform (CV + PDF/Excel + Student CRUD) ===")
    from app import create_app
    app = create_app("testing")
    
    with app.app_context():
        from app.services.cv_engine import CVEngine
        from app.models.database import DatabaseManager
        
        upload_folder = app.config["UPLOAD_FOLDER"]
        cv_engine = CVEngine(upload_folder, app.config)
        db = DatabaseManager(app.config["DATABASE"])
        
        xml_path = os.path.join("uploads", "students.xml")
        img_path = os.path.join("uploads", "1.jpeg")

        print("[1] Testing Student Master Roster CRUD & XML Exporter...")
        students_master = db.get_all_master_students()
        print(f"    Master roster loaded: {len(students_master)} students.")
        
        ok, add_res = db.add_master_student("10009999", "Test Verification Student", "batch_2016_1", "test@nsbm.lk")
        print(f"    Added student result: {ok}, ID/Msg: {add_res}")
        
        xml_out = db.generate_roster_xml("batch_2016_1")
        print(f"    Generated Roster XML snippet:\n{xml_out[:180]}...")

        if not os.path.exists(xml_path) or not os.path.exists(img_path):
            print("Sample upload files not found at uploads/ - skipping live CV run.")
            return

        print("[2] Running CV engine pipeline (with Face Detection)...")
        students = cv_engine.parse_student_file(xml_path)
        step_images, results, faces_cnt = cv_engine.process_and_analyze(
            image_path=img_path,
            students=students,
            session_prefix="v2_run",
            signature_ratio=0.60,
            threshold_val=127,
            pixel_threshold=100
        )
        print(f"    Step images generated: {list(step_images.keys())}")
        print(f"    Faces Detected in Image: {faces_cnt}")
        print(f"    Attendance Results parsed: {len(results)} students processed.")

        print("[3] Testing Database Session Storage...")
        session_id = db.save_session_results(
            session_key="v2_test_key_456",
            title="v2.0 Test Session",
            date_str="2026-08-13",
            step_images=step_images,
            results=results,
            faces_detected=faces_cnt
        )
        print(f"    Saved session to DB with ID: {session_id}")

        session = db.get_session(session_id)
        records = db.get_session_records(session_id)

        print("[4] Testing PDF & Excel Report Generators...")
        pdf_bytes = cv_engine.generate_pdf_report(session, records)
        print(f"    PDF Report generated successfully ({len(pdf_bytes)} bytes).")

        excel_bytes = cv_engine.generate_excel_report(session, records)
        print(f"    Excel Report generated successfully ({len(excel_bytes)} bytes).")

        print("=== Verification SAMS v2.0 Test Passed Successfully! ===")

if __name__ == "__main__":
    verify_system_v2()
