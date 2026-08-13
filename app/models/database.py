import os
import sqlite3
from flask import g

class DatabaseManager:
    """Manages SQLite database connection and queries for SAMS"""

    def __init__(self, db_path):
        self.db_path = db_path
        self.init_db()

    def get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def init_db(self):
        """Creates table schemas if they do not exist"""
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
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

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

        # Migration helper for legacy attendance table if present
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

    def save_session_results(self, session_key, title, date_str, step_images, results):
        """Saves session metadata and student attendance records"""
        conn = self.get_connection()
        cursor = conn.cursor()

        total = len(results)
        present = sum(1 for r in results if r["status"] == "Present")
        absent = total - present

        cursor.execute("""
            INSERT INTO sessions 
            (session_key, title, date_str, original_image, annotated_image, grayscale_image, thresh_image, total_students, present_count, absent_count)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
            absent
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

            # Legacy fallback insertion
            cursor.execute("""
                INSERT INTO attendance (date, student_index, student_name, status)
                VALUES (?, ?, ?, ?)
            """, (date_str, record["index"], record["name"], record["status"]))

        conn.commit()
        conn.close()
        return session_id

    def get_session(self, session_id_or_key):
        """Retrieve session by ID or key string"""
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
        """Get all attendance records for a session"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM attendance_records WHERE session_id = ? ORDER BY id ASC", (session_id,))
        rows = cursor.fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def toggle_record_status(self, record_id):
        """Toggle status between Present and Absent manually"""
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

        # Recalculate session statistics
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
        """Retrieve recent sessions"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM sessions ORDER BY created_at DESC LIMIT ?", (limit,))
        rows = cursor.fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def get_analytics_summary(self):
        """Get aggregate statistics for analytics dashboard"""
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
