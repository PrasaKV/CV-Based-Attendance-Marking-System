"""
Dashboard utilities for statistics and analytics
"""
from typing import Dict, List
from datetime import datetime, timedelta


class DashboardManager:
    """Generate dashboard statistics and analytics"""
    
    def __init__(self, db):
        self.db = db
    
    def get_overview_stats(self) -> Dict:
        """Get overall attendance overview"""
        stats = self.db.get_attendance_stats()
        
        return {
            "total_records": stats.get("total_records", 0),
            "total_present": stats.get("present", 0),
            "total_absent": stats.get("absent", 0),
            "present_percentage": round(stats.get("present_percentage", 0), 2),
            "absent_percentage": round(stats.get("absent_percentage", 0), 2)
        }
    
    def get_student_performance(self, days: int = 30) -> List[Dict]:
        """Get student attendance performance over last N days"""
        students = self.db.get_all_students()
        performance = []
        
        for student in students:
            attendance = self.db.get_student_attendance(
                student["student_index"],
                days=days
            )
            
            if attendance:
                total = len(attendance)
                present = sum(1 for a in attendance if a["status"] == "Present")
                percentage = (present / total * 100) if total > 0 else 0
                
                performance.append({
                    "student_index": student["student_index"],
                    "student_name": student["student_name"],
                    "total_days": total,
                    "present_days": present,
                    "absent_days": total - present,
                    "attendance_percentage": round(percentage, 2)
                })
        
        # Sort by attendance percentage
        performance.sort(key=lambda x: x["attendance_percentage"], reverse=True)
        return performance
    
    def get_daily_summary(self, date: str) -> Dict:
        """Get summary for a specific date"""
        records = self.db.get_attendance_by_date(date)
        
        if not records:
            return {
                "date": date,
                "total_students": 0,
                "present": 0,
                "absent": 0,
                "percentage": 0
            }
        
        total = len(records)
        present = sum(1 for r in records if r["status"] == "Present")
        absent = total - present
        
        return {
            "date": date,
            "total_students": total,
            "present": present,
            "absent": absent,
            "percentage": round(present / total * 100, 2) if total > 0 else 0
        }
    
    def get_trends(self, days: int = 7) -> List[Dict]:
        """Get attendance trends over last N days"""
        trends = []
        
        for i in range(days):
            date = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
            summary = self.get_daily_summary(date)
            trends.append(summary)
        
        # Reverse to show oldest first
        return list(reversed(trends))
    
    def get_top_performers(self, limit: int = 10, days: int = 30) -> List[Dict]:
        """Get top performing students"""
        performance = self.get_student_performance(days=days)
        return performance[:limit]
    
    def get_attendance_alerts(self, threshold: float = 75.0) -> List[Dict]:
        """Get students below attendance threshold"""
        performance = self.get_student_performance(days=30)
        alerts = [
            p for p in performance 
            if p["attendance_percentage"] < threshold
        ]
        return alerts
    
    def get_department_stats(self) -> Dict:
        """Get overall department statistics"""
        stats = self.get_overview_stats()
        performance = self.get_student_performance()
        
        if performance:
            avg_attendance = sum(p["attendance_percentage"] for p in performance) / len(performance)
        else:
            avg_attendance = 0
        
        return {
            **stats,
            "total_students": len(self.db.get_all_students()),
            "average_attendance_percentage": round(avg_attendance, 2)
        }
