import sqlite3


class AttendanceDatabase:
    """Handles persistence of attendance records to SQLite."""

    def __init__(self, db_path="attendance.db"):
        self.db_path = db_path
        self._ensure_schema()

    def _connect(self):
        return sqlite3.connect(self.db_path)

    def _ensure_schema(self):
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS attendance (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date TEXT,
                    student_index TEXT,
                    student_name TEXT,
                    status TEXT
                )
                """
            )

    def record_batch(self, date, entries):
        """Persist a batch of attendance entries.

        entries: iterable of dicts with keys 'index', 'name', 'status'.
        """
        with self._connect() as conn:
            conn.executemany(
                """
                INSERT INTO attendance (date, student_index, student_name, status)
                VALUES (?, ?, ?, ?)
                """,
                [(date, e["index"], e["name"], e["status"]) for e in entries],
            )
