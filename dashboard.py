"""
Dashboard and Analytics Engine (v2.0)
Provides comprehensive statistical summaries, student performance metrics,
attendance trends, defaulter alerts, and batch-wise analytics for SAMS.
"""

from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import sqlite3


class DashboardManager:
    """Advanced attendance statistics, analytics, and risk forecasting manager."""

    DEFAULT_ALERT_THRESHOLD = 75.0  # Percentage below which students are flagged

    def __init__(self, db: Any):
        """
        Initialize with either a DatabaseManager instance, SQLite connection,
        or database file path.
        """
        self.db = db

    def _get_connection(self) -> sqlite3.Connection:
        """Internal helper to obtain a standardized SQLite connection with Row factory."""
        if hasattr(self.db, "get_connection"):
            return self.db.get_connection()
        elif hasattr(self.db, "cursor"):
            return self.db
        elif isinstance(self.db, str):
            conn = sqlite3.connect(self.db)
            conn.row_factory = sqlite3.Row
            return conn
        elif hasattr(self.db, "db_path"):
            conn = sqlite3.connect(self.db.db_path)
            conn.row_factory = sqlite3.Row
            return conn
        elif hasattr(self.db, "db_name"):
            conn = sqlite3.connect(self.db.db_name)
            conn.row_factory = sqlite3.Row
            return conn
        else:
            conn = sqlite3.connect("attendance.db")
            conn.row_factory = sqlite3.Row
            return conn

    # =========================================================================
    # High-Level Overview Metrics
    # =========================================================================

    def get_overview_stats(self) -> Dict[str, Any]:
        """
        Retrieve high-level overview metrics across all sessions and records.
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            # Query sessions table
            cursor.execute("""
                SELECT 
                    COUNT(*) as total_sessions,
                    COALESCE(SUM(total_students), 0) as total_markings,
                    COALESCE(SUM(present_count), 0) as total_present,
                    COALESCE(SUM(absent_count), 0) as total_absent,
                    COALESCE(SUM(faces_detected), 0) as total_faces_detected
                FROM sessions
            """)
            row = cursor.fetchone()

            total_sessions = row["total_sessions"] if row else 0
            total_records = row["total_markings"] if row else 0
            total_present = row["total_present"] if row else 0
            total_absent = row["total_absent"] if row else 0
            total_faces = row["total_faces_detected"] if row else 0

            # Fallback to legacy attendance table if sessions is empty
            if total_sessions == 0 and total_records == 0:
                cursor.execute("""
                    SELECT 
                        COUNT(DISTINCT date) as total_sessions,
                        COUNT(*) as total_markings,
                        SUM(CASE WHEN status = 'Present' THEN 1 ELSE 0 END) as total_present,
                        SUM(CASE WHEN status = 'Absent' THEN 1 ELSE 0 END) as total_absent
                    FROM attendance
                """)
                legacy_row = cursor.fetchone()
                if legacy_row and legacy_row["total_markings"]:
                    total_sessions = legacy_row["total_sessions"] or 0
                    total_records = legacy_row["total_markings"] or 0
                    total_present = legacy_row["total_present"] or 0
                    total_absent = legacy_row["total_absent"] or 0

            present_rate = (total_present / total_records * 100) if total_records > 0 else 0.0
            absent_rate = (total_absent / total_records * 100) if total_records > 0 else 0.0

            # Count unique registered students
            cursor.execute("SELECT COUNT(*) as cnt FROM master_students")
            registered_students = cursor.fetchone()["cnt"]

            # Count manual overrides
            cursor.execute("""
                SELECT COUNT(*) as cnt 
                FROM attendance_records 
                WHERE is_manually_overridden = 1
            """)
            overridden_count = cursor.fetchone()["cnt"]

            return {
                "total_sessions": total_sessions,
                "total_records": total_records,
                "total_present": total_present,
                "total_absent": total_absent,
                "present_percentage": round(present_rate, 2),
                "absent_percentage": round(absent_rate, 2),
                "registered_students": registered_students,
                "manual_overrides": overridden_count,
                "total_faces_detected": total_faces
            }

        except Exception as e:
            print(f"[DashboardManager] Error in get_overview_stats: {e}")
            return {
                "total_sessions": 0,
                "total_records": 0,
                "total_present": 0,
                "total_absent": 0,
                "present_percentage": 0.0,
                "absent_percentage": 0.0,
                "registered_students": 0,
                "manual_overrides": 0,
                "total_faces_detected": 0
            }
        finally:
            conn.close()

    # =========================================================================
    # Student Performance & Risk Analysis
    # =========================================================================

    def get_student_performance(
        self,
        days: int = 30,
        batch: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Calculate individual student attendance percentages, present/absent counts,
        streak lengths, and risk categories over the last N days.
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        performance = []
        try:
            # Determine date cutoff if days filter is given
            cutoff_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")

            # Fetch students from master_students table
            if batch:
                cursor.execute("""
                    SELECT student_index, student_name, batch, email 
                    FROM master_students 
                    WHERE batch = ? 
                    ORDER BY student_index ASC
                """, (batch,))
            else:
                cursor.execute("""
                    SELECT student_index, student_name, batch, email 
                    FROM master_students 
                    ORDER BY student_index ASC
                """)

            students = [dict(r) for r in cursor.fetchall()]

            # If no master students exist, extract unique students from attendance records
            if not students:
                cursor.execute("""
                    SELECT DISTINCT student_index, student_name, 'general' as batch, '' as email
                    FROM attendance_records
                    ORDER BY student_index ASC
                """)
                students = [dict(r) for r in cursor.fetchall()]

            for student in students:
                s_idx = student["student_index"]

                # Query attendance records joined with sessions for date filtering
                cursor.execute("""
                    SELECT 
                        ar.status,
                        s.date_str as date_val
                    FROM attendance_records ar
                    LEFT JOIN sessions s ON ar.session_id = s.id
                    WHERE ar.student_index = ?
                      AND (s.date_str >= ? OR s.date_str IS NULL)
                    ORDER BY s.date_str DESC
                """, (s_idx, cutoff_date))

                records = cursor.fetchall()

                # Fallback to legacy attendance table if no records in attendance_records
                if not records:
                    try:
                        cursor.execute("""
                            SELECT status, date as date_val 
                            FROM attendance 
                            WHERE student_index = ? 
                              AND date >= ?
                            ORDER BY date DESC
                        """, (s_idx, cutoff_date))
                        records = cursor.fetchall()
                    except sqlite3.OperationalError:
                        records = []

                total_days = len(records)
                present_days = sum(1 for r in records if r["status"] == "Present")
                absent_days = total_days - present_days
                percentage = (present_days / total_days * 100) if total_days > 0 else 0.0

                # Calculate current consecutive streak (from latest record backwards)
                current_streak = 0
                for r in records:
                    if r["status"] == "Present":
                        current_streak += 1
                    else:
                        break

                # Risk categorization
                if total_days == 0:
                    risk_level = "No Data"
                    badge_color = "secondary"
                elif percentage >= 80.0:
                    risk_level = "Good Standing"
                    badge_color = "success"
                elif percentage >= 65.0:
                    risk_level = "Warning / Moderate"
                    badge_color = "warning"
                else:
                    risk_level = "Critical / Defaulter"
                    badge_color = "danger"

                # Calculate required classes to recover to 75%
                classes_needed = 0
                if total_days > 0 and percentage < self.DEFAULT_ALERT_THRESHOLD:
                    # Formula: (present + x) / (total + x) >= 0.75 => x >= (0.75*total - present) / 0.25
                    shortfall = (0.75 * total_days - present_days) / 0.25
                    classes_needed = max(1, int(round(shortfall)))

                performance.append({
                    "student_index": s_idx,
                    "student_name": student["student_name"],
                    "batch": student.get("batch", "general"),
                    "email": student.get("email", ""),
                    "total_days": total_days,
                    "present_days": present_days,
                    "absent_days": absent_days,
                    "attendance_percentage": round(percentage, 2),
                    "current_streak": current_streak,
                    "risk_level": risk_level,
                    "badge_color": badge_color,
                    "classes_needed_for_75": classes_needed
                })

            # Sort descending by attendance percentage, then by name
            performance.sort(key=lambda x: (x["attendance_percentage"], x["present_days"]), reverse=True)
            return performance

        except Exception as e:
            print(f"[DashboardManager] Error in get_student_performance: {e}")
            return []
        finally:
            conn.close()

    def get_attendance_alerts(
        self,
        threshold: float = DEFAULT_ALERT_THRESHOLD,
        days: int = 30
    ) -> List[Dict[str, Any]]:
        """
        Get list of students whose attendance is strictly below the given threshold.
        """
        performance = self.get_student_performance(days=days)
        alerts = [
            p for p in performance
            if p["total_days"] > 0 and p["attendance_percentage"] < threshold
        ]
        # Sort lowest percentage first to prioritize critical students
        alerts.sort(key=lambda x: x["attendance_percentage"])
        return alerts

    def get_top_performers(
        self,
        limit: int = 10,
        days: int = 30
    ) -> List[Dict[str, Any]]:
        """Get top performing students with highest attendance."""
        performance = self.get_student_performance(days=days)
        active = [p for p in performance if p["total_days"] > 0]
        return active[:limit]

    def get_at_risk_students(
        self,
        limit: int = 10,
        days: int = 30
    ) -> List[Dict[str, Any]]:
        """Get students with lowest attendance who need immediate academic attention."""
        alerts = self.get_attendance_alerts(threshold=self.DEFAULT_ALERT_THRESHOLD, days=days)
        return alerts[:limit]

    # =========================================================================
    # Time-Series Trends & Daily Summaries
    # =========================================================================

    def get_daily_summary(self, date: str) -> Dict[str, Any]:
        """Get aggregate attendance statistics for a specific calendar date."""
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            # Query sessions table
            cursor.execute("""
                SELECT 
                    SUM(total_students) as total,
                    SUM(present_count) as present,
                    SUM(absent_count) as absent
                FROM sessions
                WHERE date_str = ?
            """, (date,))
            row = cursor.fetchone()

            if row and row["total"] is not None and row["total"] > 0:
                total = row["total"]
                present = row["present"]
                absent = row["absent"]
            else:
                # Fallback to legacy attendance table if present
                try:
                    cursor.execute("""
                        SELECT 
                            COUNT(*) as total,
                            SUM(CASE WHEN status = 'Present' THEN 1 ELSE 0 END) as present,
                            SUM(CASE WHEN status = 'Absent' THEN 1 ELSE 0 END) as absent
                        FROM attendance
                        WHERE date = ?
                    """, (date,))
                    leg_row = cursor.fetchone()
                    total = leg_row["total"] if leg_row else 0
                    present = leg_row["present"] if leg_row else 0
                    absent = leg_row["absent"] if leg_row else 0
                except sqlite3.OperationalError:
                    total, present, absent = 0, 0, 0

            rate = (present / total * 100) if total > 0 else 0.0

            return {
                "date": date,
                "total_students": total or 0,
                "present": present or 0,
                "absent": absent or 0,
                "percentage": round(rate, 2)
            }

        except Exception as e:
            print(f"[DashboardManager] Error in get_daily_summary: {e}")
            return {
                "date": date,
                "total_students": 0,
                "present": 0,
                "absent": 0,
                "percentage": 0.0
            }
        finally:
            conn.close()

    def get_trends(self, days: int = 14) -> List[Dict[str, Any]]:
        """
        Get daily attendance trends over the last N days (oldest date to newest).
        """
        trends = []
        for i in range(days):
            date_str = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
            summary = self.get_daily_summary(date_str)
            trends.append(summary)

        # Reverse so earliest dates appear first (ideal for charting)
        return list(reversed(trends))

    def get_day_of_week_analysis(self) -> Dict[str, Any]:
        """
        Analyze average attendance performance grouped by Day of the Week (Monday - Sunday).
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        day_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        day_stats = {name: {"sessions": 0, "total": 0, "present": 0, "average_percentage": 0.0} for name in day_names}

        try:
            cursor.execute("SELECT date_str, total_students, present_count FROM sessions")
            rows = cursor.fetchall()

            for r in rows:
                date_str = r["date_str"]
                try:
                    dt = datetime.strptime(date_str, "%Y-%m-%d")
                    day_name = day_names[dt.weekday()]
                    day_stats[day_name]["sessions"] += 1
                    day_stats[day_name]["total"] += (r["total_students"] or 0)
                    day_stats[day_name]["present"] += (r["present_count"] or 0)
                except ValueError:
                    continue

            for name, data in day_stats.items():
                if data["total"] > 0:
                    data["average_percentage"] = round((data["present"] / data["total"]) * 100, 2)

            return day_stats

        except Exception as e:
            print(f"[DashboardManager] Error in get_day_of_week_analysis: {e}")
            return day_stats
        finally:
            conn.close()

    # =========================================================================
    # Batch & Department Summaries
    # =========================================================================

    def get_batch_wise_statistics(self) -> List[Dict[str, Any]]:
        """
        Compare attendance rates across different student batches.
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        batch_list = []
        try:
            cursor.execute("""
                SELECT DISTINCT batch 
                FROM master_students 
                WHERE batch IS NOT NULL AND batch != ''
            """)
            batches = [r["batch"] for r in cursor.fetchall()]

            if not batches:
                batches = ["default"]

            for b in batches:
                perf = self.get_student_performance(days=60, batch=b)
                active = [p for p in perf if p["total_days"] > 0]

                if active:
                    avg_rate = sum(p["attendance_percentage"] for p in active) / len(active)
                    defaulters = sum(1 for p in active if p["attendance_percentage"] < self.DEFAULT_ALERT_THRESHOLD)
                else:
                    avg_rate = 0.0
                    defaulters = 0

                batch_list.append({
                    "batch": b,
                    "total_students": len(perf),
                    "active_students": len(active),
                    "average_attendance": round(avg_rate, 2),
                    "defaulter_count": defaulters
                })

            batch_list.sort(key=lambda x: x["average_attendance"], reverse=True)
            return batch_list

        except Exception as e:
            print(f"[DashboardManager] Error in get_batch_wise_statistics: {e}")
            return []
        finally:
            conn.close()

    def get_department_stats(self) -> Dict[str, Any]:
        """Get overall institutional / department statistics."""
        overview = self.get_overview_stats()
        performance = self.get_student_performance(days=30)

        active = [p for p in performance if p["total_days"] > 0]
        avg_rate = (sum(p["attendance_percentage"] for p in active) / len(active)) if active else 0.0
        alerts = [p for p in active if p["attendance_percentage"] < self.DEFAULT_ALERT_THRESHOLD]

        return {
            **overview,
            "total_students": len(performance),
            "active_students": len(active),
            "average_attendance_percentage": round(avg_rate, 2),
            "defaulter_count": len(alerts),
            "defaulter_rate": round((len(alerts) / len(active) * 100), 2) if active else 0.0
        }

    # =========================================================================
    # Unified Export Payload
    # =========================================================================

    def get_full_dashboard_payload(self) -> Dict[str, Any]:
        """
        Produce a comprehensive analytics dictionary suitable for single-request
        REST API endpoints or frontend UI rendering.
        """
        return {
            "overview": self.get_overview_stats(),
            "department": self.get_department_stats(),
            "trends_14_days": self.get_trends(days=14),
            "day_of_week": self.get_day_of_week_analysis(),
            "batches": self.get_batch_wise_statistics(),
            "top_performers": self.get_top_performers(limit=5),
            "defaulter_alerts": self.get_at_risk_students(limit=10)
        }
