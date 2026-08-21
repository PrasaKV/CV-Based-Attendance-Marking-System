import os
import sqlite3
import xml.etree.ElementTree as ET
from xml.dom import minidom
from flask import g

class DatabaseManager:
    """Manages SQLite database connection and queries for SAMS v2.0"""

    def __init__(self, db_path):
        self.db_path = db_path
        self.init_db()

    def get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def init_db(self):
        """Creates table schemas if they do not exist and applies migrations"""
        conn = self.get_connection()
        cursor = conn.cursor()

        # Sessions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_key TEXT UNIQUE,
                title TEXT,
                date_str TEXT,
                original_image TEXT,
                annotated_image TEXT,
                grayscale_image TEXT,
                thresh_image TEXT,
                total_students INTEGER DEFAULT 0,
                present_count INTEGER DEFAULT 0,
                absent_count INTEGER DEFAULT 0,
                faces_detected INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Migration: Ensure faces_detected column exists if table was created previously
        cursor.execute("PRAGMA table_info(sessions)")
        columns = [col[1] for col in cursor.fetchall()]
        if "faces_detected" not in columns:
            try:
                cursor.execute("ALTER TABLE sessions ADD COLUMN faces_detected INTEGER DEFAULT 0")
            except Exception as e:
                print(f"[DB Migration] Column addition notice: {e}")

        # Attendance Records table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS attendance_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id INTEGER,
                student_index TEXT,
                student_name TEXT,
                status TEXT,
                original_status TEXT,
                pixel_count INTEGER,
                crop_image TEXT,
                is_manually_overridden INTEGER DEFAULT 0,
                FOREIGN KEY (session_id) REFERENCES sessions (id) ON DELETE CASCADE
            )
        """)

        # Master Students table for Roster CRUD
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS master_students (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_index TEXT UNIQUE,
                student_name TEXT,
                batch TEXT DEFAULT 'batch_2016_1',
                email TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Seed initial sample students if table is empty
        cursor.execute("SELECT COUNT(*) as cnt FROM master_students")
        if cursor.fetchone()["cnt"] == 0:
            sample_students = [
                ("10000409", "M S Dilshanika Perera", "batch_2016_1", "dilshanika@nsbm.lk"),
                ("10009301", "C W M A Shehan Abeyrathne", "batch_2016_1", "shehan@nsbm.lk"),
                ("10009302", "B A K M Chithrananda", "batch_2016_1", "chithrananda@nsbm.lk"),
                ("10009303", "W Shashini Minosha De Silva", "batch_2016_1", "shashini@nsbm.lk"),
                ("10009304", "K L Udara Maduranga Liyanage", "batch_2016_1", "udara@nsbm.lk"),
                ("10009306", "Hansa Anuradha Wickramanayake", "batch_2016_1", "hansa@nsbm.lk"),
            ]
            cursor.executemany("""
                INSERT INTO master_students (student_index, student_name, batch, email)
                VALUES (?, ?, ?, ?)
            """, sample_students)

        # Legacy table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS attendance (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT,
                student_index TEXT,
                student_name TEXT,
                status TEXT
            )
        """)

        conn.commit()
        conn.close()

    def save_session_results(self, session_key, title, date_str, step_images, results, faces_detected=0):
        """Saves session metadata and student attendance records"""
        conn = self.get_connection()
        cursor = conn.cursor()

        total = len(results)
        present = sum(1 for r in results if r["status"] == "Present")
        absent = total - present

        cursor.execute("""
            INSERT INTO sessions 
            (session_key, title, date_str, original_image, annotated_image, grayscale_image, thresh_image, total_students, present_count, absent_count, faces_detected)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            session_key,
            title,
            date_str,
            step_images.get("original", ""),
            step_images.get("annotated", ""),
            step_images.get("grayscale", ""),
            step_images.get("binarized", ""),
            total,
            present,
            absent,
            faces_detected
        ))
        session_id = cursor.lastrowid

        for record in results:
            cursor.execute("""
                INSERT INTO attendance_records
                (session_id, student_index, student_name, status, original_status, pixel_count, crop_image)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                session_id,
                record["index"],
                record["name"],
                record["status"],
                record["status"],
                record.get("pixel_count", 0),
                record.get("crop_image", "")
            ))

            cursor.execute("""
                INSERT INTO attendance (date, student_index, student_name, status)
                VALUES (?, ?, ?, ?)
            """, (date_str, record["index"], record["name"], record["status"]))

        conn.commit()
        conn.close()
        return session_id

    def get_session(self, session_id_or_key):
        conn = self.get_connection()
        cursor = conn.cursor()

        if str(session_id_or_key).isdigit():
            cursor.execute("SELECT * FROM sessions WHERE id = ?", (int(session_id_or_key),))
        else:
            cursor.execute("SELECT * FROM sessions WHERE session_key = ?", (str(session_id_or_key),))
        
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None

    def get_session_records(self, session_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM attendance_records WHERE session_id = ? ORDER BY id ASC", (session_id,))
        rows = cursor.fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def toggle_record_status(self, record_id):
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM attendance_records WHERE id = ?", (record_id,))
        record = cursor.fetchone()
        if not record:
            conn.close()
            return None

        new_status = "Absent" if record["status"] == "Present" else "Present"
        is_overridden = 1 if new_status != record["original_status"] else 0

        cursor.execute("""
            UPDATE attendance_records
            SET status = ?, is_manually_overridden = ?
            WHERE id = ?
        """, (new_status, is_overridden, record_id))

        session_id = record["session_id"]
        cursor.execute("""
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN status = 'Present' THEN 1 ELSE 0 END) as present_count,
                SUM(CASE WHEN status = 'Absent' THEN 1 ELSE 0 END) as absent_count
            FROM attendance_records
            WHERE session_id = ?
        """, (session_id,))
        stats = cursor.fetchone()

        cursor.execute("""
            UPDATE sessions
            SET present_count = ?, absent_count = ?
            WHERE id = ?
        """, (stats["present_count"], stats["absent_count"], session_id))

        conn.commit()
        conn.close()
        return {
            "record_id": record_id,
            "new_status": new_status,
            "is_overridden": bool(is_overridden),
            "present_count": stats["present_count"],
            "absent_count": stats["absent_count"]
        }

    def get_all_sessions(self, limit=50):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM sessions ORDER BY created_at DESC LIMIT ?", (limit,))
        rows = cursor.fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def get_analytics_summary(self):
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) as total_sessions FROM sessions")
        total_sessions = cursor.fetchone()["total_sessions"]

        cursor.execute("""
            SELECT 
                SUM(total_students) as total_markings,
                SUM(present_count) as total_present,
                SUM(absent_count) as total_absent
            FROM sessions
        """)
        sum_row = cursor.fetchone()
        
        total_markings = sum_row["total_markings"] or 0
        total_present = sum_row["total_present"] or 0
        total_absent = sum_row["total_absent"] or 0

        rate = (total_present / total_markings * 100) if total_markings > 0 else 0

        cursor.execute("""
            SELECT date_str, title, present_count, absent_count, total_students 
            FROM sessions 
            ORDER BY created_at ASC 
            LIMIT 10
        """)
        recent_trend = [dict(r) for r in cursor.fetchall()]

        conn.close()
        return {
            "total_sessions": total_sessions,
            "total_markings": total_markings,
            "total_present": total_present,
            "total_absent": total_absent,
            "attendance_rate": round(rate, 1),
            "recent_trend": recent_trend
        }

    # --- Student Master CRUD methods ---
    def get_all_master_students(self, batch=None):
        conn = self.get_connection()
        cursor = conn.cursor()
        if batch:
            cursor.execute("SELECT * FROM master_students WHERE batch = ? ORDER BY student_index ASC", (batch,))
        else:
            cursor.execute("SELECT * FROM master_students ORDER BY student_index ASC")
        rows = cursor.fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def add_master_student(self, student_index, student_name, batch="batch_2016_1", email=""):
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                INSERT INTO master_students (student_index, student_name, batch, email)
                VALUES (?, ?, ?, ?)
            """, (student_index.strip(), student_name.strip(), batch.strip(), email.strip()))
            conn.commit()
            student_id = cursor.lastrowid
            conn.close()
            return True, student_id
        except sqlite3.IntegrityError:
            conn.close()
            return False, "Student Index already exists."
        except Exception as e:
            conn.close()
            return False, str(e)

    def delete_master_student(self, student_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM master_students WHERE id = ?", (student_id,))
        conn.commit()
        conn.close()
        return True

    def generate_roster_xml(self, batch="batch_2016_1"):
        students = self.get_all_master_students(batch)
        
        nsbm = ET.Element("nsbm")
        students_elem = ET.SubElement(nsbm, "students")
        batches_elem = ET.SubElement(students_elem, "batches")
        batch_elem = ET.SubElement(batches_elem, batch)

        for s in students:
            student_elem = ET.SubElement(batch_elem, "student")
            idx_elem = ET.SubElement(student_elem, "index")
            idx_elem.text = s["student_index"]
            name_elem = ET.SubElement(student_elem, "name")
            name_elem.text = s["student_name"]

        raw_str = ET.tostring(nsbm, encoding="utf-8")
        parsed = minidom.parseString(raw_str)
        return parsed.toprettyxml(indent="    ")

    # ===== AUTO-GENERATED DATABASE METHODS =====

    def get_record(self, record_id):
        """Get a specific attendance record by ID"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM attendance_records WHERE id = ?", (record_id,))
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None

    def create_record(self, session_id, data):
        """Create a new attendance record"""
        conn = self.get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("""
                INSERT INTO attendance_records
                (session_id, student_index, student_name, status, original_status, pixel_count, crop_image)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                session_id,
                data.get("student_index", ""),
                data.get("student_name", ""),
                data.get("status", "Absent"),
                data.get("status", "Absent"),
                data.get("pixel_count", 0),
                data.get("crop_image", "")
            ))
            record_id = cursor.lastrowid
            conn.commit()
            conn.close()
            return record_id
        except Exception as e:
            conn.close()
            return None

    def update_record(self, record_id, data):
        """Update an attendance record"""
        conn = self.get_connection()
        cursor = conn.cursor()

        record = self.get_record(record_id)
        if not record:
            conn.close()
            return None

        # Update status if provided
        if "status" in data:
            new_status = data["status"]
            is_overridden = 1 if new_status != record["original_status"] else 0

            cursor.execute("""
                UPDATE attendance_records
                SET status = ?, is_manually_overridden = ?
                WHERE id = ?
            """, (new_status, is_overridden, record_id))
        
        # Update other fields
        if "student_name" in data:
            cursor.execute("UPDATE attendance_records SET student_name = ? WHERE id = ?",
                          (data["student_name"], record_id))
        if "pixel_count" in data:
            cursor.execute("UPDATE attendance_records SET pixel_count = ? WHERE id = ?",
                          (data["pixel_count"], record_id))
        if "crop_image" in data:
            cursor.execute("UPDATE attendance_records SET crop_image = ? WHERE id = ?",
                          (data["crop_image"], record_id))

        conn.commit()
        conn.close()
        return self.get_record(record_id)

    def delete_session(self, session_id):
        """Delete a session and all associated records"""
        conn = self.get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("DELETE FROM attendance_records WHERE session_id = ?", (session_id,))
            cursor.execute("DELETE FROM sessions WHERE id = ?", (session_id,))
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            conn.close()
            return False

    def delete_record(self, record_id):
        """Delete a specific attendance record"""
        conn = self.get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("DELETE FROM attendance_records WHERE id = ?", (record_id,))
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            conn.close()
            return False

    def get_all_unique_students(self):
        """Get all unique students from all sessions"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT DISTINCT student_index, student_name 
            FROM attendance_records 
            ORDER BY student_index ASC
        """)
        rows = cursor.fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def get_student_attendance_history(self, student_index):
        """Get attendance history for a specific student"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT 
                ar.*, 
                s.date_str, s.title, s.created_at
            FROM attendance_records ar
            JOIN sessions s ON ar.session_id = s.id
            WHERE ar.student_index = ?
            ORDER BY s.created_at DESC
        """, (student_index,))
        rows = cursor.fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def search_sessions(self, query):
        """Search sessions by date or title"""
        conn = self.get_connection()
        cursor = conn.cursor()
        query_pattern = f"%{query}%"
        cursor.execute("""
            SELECT * FROM sessions 
            WHERE date_str LIKE ? OR title LIKE ? OR session_key LIKE ?
            ORDER BY created_at DESC
        """, (query_pattern, query_pattern, query_pattern))
        rows = cursor.fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def get_sessions_by_date_range(self, start_date, end_date):
        """Get sessions within a date range"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM sessions 
            WHERE date_str BETWEEN ? AND ?
            ORDER BY created_at DESC
        """, (start_date, end_date))
        rows = cursor.fetchall()
        conn.close()
        return [dict(r) for r in rows]

