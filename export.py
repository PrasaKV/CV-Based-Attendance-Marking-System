"""
Export utilities for attendance data
"""
import csv
import json
import os
from datetime import datetime
from typing import List, Dict
from config import Config


class ExportManager:
    """Handle exporting attendance data"""
    
    @staticmethod
    def export_to_csv(
        records: List[Dict],
        filename: str = None
    ) -> str:
        """Export attendance records to CSV"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"attendance_{timestamp}.csv"
        
        filepath = os.path.join(Config.UPLOAD_FOLDER, filename)
        
        try:
            with open(filepath, 'w', newline='') as csvfile:
                if not records:
                    return None
                
                fieldnames = records[0].keys()
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                
                writer.writeheader()
                writer.writerows(records)
            
            return filepath
        except Exception as e:
            print(f"Error exporting to CSV: {e}")
            return None
    
    @staticmethod
    def export_to_json(
        records: List[Dict],
        filename: str = None
    ) -> str:
        """Export attendance records to JSON"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"attendance_{timestamp}.json"
        
        filepath = os.path.join(Config.UPLOAD_FOLDER, filename)
        
        try:
            with open(filepath, 'w') as jsonfile:
                json.dump(records, jsonfile, indent=2, default=str)
            
            return filepath
        except Exception as e:
            print(f"Error exporting to JSON: {e}")
            return None
    
    @staticmethod
    def export_attendance_report(
        records: List[Dict],
        format: str = "csv"
    ) -> str:
        """Export detailed attendance report"""
        if format == "csv":
            return ExportManager.export_to_csv(records)
        elif format == "json":
            return ExportManager.export_to_json(records)
        else:
            return None
    
    @staticmethod
    def generate_summary_report(stats: Dict, filename: str = None) -> str:
        """Generate summary statistics report"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"report_{timestamp}.txt"
        
        filepath = os.path.join(Config.UPLOAD_FOLDER, filename)
        
        try:
            with open(filepath, 'w') as f:
                f.write("ATTENDANCE SUMMARY REPORT\n")
                f.write("=" * 50 + "\n")
                f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                
                f.write("STATISTICS:\n")
                f.write(f"Total Records: {stats.get('total_records', 0)}\n")
                f.write(f"Present: {stats.get('present', 0)} ({stats.get('present_percentage', 0):.2f}%)\n")
                f.write(f"Absent: {stats.get('absent', 0)} ({stats.get('absent_percentage', 0):.2f}%)\n")
            
            return filepath
        except Exception as e:
            print(f"Error generating report: {e}")
            return None
