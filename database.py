"""
Database operations and queries
"""
import sqlite3
from datetime import datetime
from typing import List, Dict, Optional
from config import Config


class Database:
    """Database operations for attendance system"""
    
    def __init__(self, db_name=None):
        self.db_name = db_name or Config.DATABASE
        self.init_db()
    
    def init_db(self):
        """Initialize database with all tables"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        # Attendance table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS attendance (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT,
                student_index TEXT,
                student_name TEXT,
                status TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        
        # Students table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS students (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_index TEXT UNIQUE NOT NULL,
                student_name TEXT NOT NULL,
                email TEXT,
                phone TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        
        conn.commit()
        conn.close()
    
    def add_student(self, index: str, name: str, email: str = None, phone: str = None) -> bool:
        """Add a new student"""
        try:
            conn = sqlite3.connect(self.db_name)
            cursor = conn.cursor()
            
            cursor.execute(
                """
                INSERT INTO students 
                (student_index, student_name, email, phone)
                VALUES (?, ?, ?, ?)
                """,
                (index, name, email, phone)
            )
            
            conn.commit()
            conn.close()
            return True
        except sqlite3.IntegrityError:
            return False
        except Exception as e:
            print(f"Error adding student: {e}")
            return False
    
    def get_student(self, index: str) -> Optional[Dict]:
        """Get student by index"""
        conn = sqlite3.connect(self.db_name)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT * FROM students WHERE student_index = ?",
            (index,)
        )
        
        row = cursor.fetchone()
        conn.close()
        
        return dict(row) if row else None
    
    def get_all_students(self) -> List[Dict]:
        """Get all students"""
        conn = sqlite3.connect(self.db_name)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM students ORDER BY student_index")
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]
    
    def update_student(self, index: str, name: str = None, email: str = None, phone: str = None) -> bool:
        """Update student information"""
        try:
            conn = sqlite3.connect(self.db_name)
            cursor = conn.cursor()
            
            updates = []
            params = []
            
            if name:
                updates.append("student_name = ?")
                params.append(name)
            if email:
                updates.append("email = ?")
                params.append(email)
            if phone:
                updates.append("phone = ?")
                params.append(phone)
            
            updates.append("updated_at = CURRENT_TIMESTAMP")
            params.append(index)
            
            if len(updates) > 1:  # More than just updated_at
                query = f"UPDATE students SET {', '.join(updates)} WHERE student_index = ?"
                cursor.execute(query, params)
                conn.commit()
            
            conn.close()
            return True
        except Exception as e:
            print(f"Error updating student: {e}")
            return False
    
    def delete_student(self, index: str) -> bool:
        """Delete student"""
        try:
            conn = sqlite3.connect(self.db_name)
            cursor = conn.cursor()
            
            cursor.execute("DELETE FROM students WHERE student_index = ?", (index,))
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Error deleting student: {e}")
            return False
    
    def get_attendance_records(
        self,
        date: str = None,
        student_index: str = None,
        status: str = None,
        limit: int = 100
    ) -> List[Dict]:
        """Get attendance records with filtering"""
        conn = sqlite3.connect(self.db_name)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        query = "SELECT * FROM attendance WHERE 1=1"
        params = []
        
        if date:
            query += " AND date = ?"
            params.append(date)
        if student_index:
            query += " AND student_index = ?"
            params.append(student_index)
        if status:
            query += " AND status = ?"
            params.append(status)
        
        query += " ORDER BY date DESC, student_index LIMIT ?"
        params.append(limit)
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]
    
    def get_attendance_by_date(self, date: str) -> List[Dict]:
        """Get all attendance records for a specific date"""
        return self.get_attendance_records(date=date, limit=1000)
    
    def get_student_attendance(self, student_index: str, days: int = 30) -> List[Dict]:
        """Get attendance history for a student"""
        conn = sqlite3.connect(self.db_name)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute(
            """
            SELECT * FROM attendance 
            WHERE student_index = ? 
            AND date >= date((SELECT MAX(date) FROM attendance), '-' || ? || ' days')
            ORDER BY date DESC
            """,
            (student_index, days)
        )
        
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]
    
    def update_attendance(self, attendance_id: int, status: str) -> bool:
        """Update attendance status"""
        try:
            conn = sqlite3.connect(self.db_name)
            cursor = conn.cursor()
            
            cursor.execute(
                "UPDATE attendance SET status = ? WHERE id = ?",
                (status, attendance_id)
            )
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Error updating attendance: {e}")
            return False
    
    def insert_attendance(
        self,
        date: str,
        student_index: str,
        student_name: str,
        status: str
    ) -> bool:
        """Insert attendance record"""
        try:
            conn = sqlite3.connect(self.db_name)
            cursor = conn.cursor()
            
            cursor.execute(
                """
                INSERT INTO attendance
                (date, student_index, student_name, status)
                VALUES (?, ?, ?, ?)
                """,
                (date, student_index, student_name, status)
            )
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Error inserting attendance: {e}")
            return False
    
    def get_attendance_stats(self, start_date: str = None, end_date: str = None) -> Dict:
        """Get attendance statistics"""
        conn = sqlite3.connect(self.db_name)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        query = "SELECT * FROM attendance WHERE 1=1"
        params = []
        
        if start_date:
            query += " AND date >= ?"
            params.append(start_date)
        if end_date:
            query += " AND date <= ?"
            params.append(end_date)
        
        cursor.execute(query, params)
        records = cursor.fetchall()
        
        total_records = len(records)
        present = sum(1 for r in records if r["status"] == "Present")
        absent = sum(1 for r in records if r["status"] == "Absent")
        
        stats = {
            "total_records": total_records,
            "present": present,
            "absent": absent,
            "present_percentage": (present / total_records * 100) if total_records > 0 else 0,
            "absent_percentage": (absent / total_records * 100) if total_records > 0 else 0
        }
        
        conn.close()
        return stats
