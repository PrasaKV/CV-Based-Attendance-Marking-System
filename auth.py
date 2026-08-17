"""
Authentication module for user management.
"""

import sqlite3
import secrets
import hashlib
import hmac
from datetime import datetime, timedelta
from typing import Optional, Dict


class PasswordManager:
    """Handle password hashing and verification."""

    ITERATIONS = 100_000
    SALT_LENGTH = 16

    @staticmethod
    def hash_password(password: str) -> str:
        """Generate a salted PBKDF2 password hash."""

        salt = secrets.token_bytes(PasswordManager.SALT_LENGTH)

        password_hash = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt,
            PasswordManager.ITERATIONS
        )

        return (
            f"{PasswordManager.ITERATIONS}$"
            f"{salt.hex()}$"
            f"{password_hash.hex()}"
        )

    @staticmethod
    def verify_password(password: str, stored_hash: str) -> bool:
        """Verify a password against the stored hash."""

        try:
            iterations, salt_hex, hash_hex = stored_hash.split("$")

            salt = bytes.fromhex(salt_hex)

            password_hash = hashlib.pbkdf2_hmac(
                "sha256",
                password.encode("utf-8"),
                salt,
                int(iterations)
            )

            return hmac.compare_digest(
                password_hash.hex(),
                hash_hex
            )

        except (ValueError, TypeError):
            return False


class AuthManager:
    """Manage registration, login, sessions and logout."""

    SESSION_DURATION = timedelta(hours=24)

    def __init__(self, db):
        self.db = db
        self.sessions: Dict[str, Dict] = {}

        self.initialize_database()

    def get_connection(self):
        """Create a database connection."""

        return sqlite3.connect(self.db.db_name)

    def initialize_database(self):
        """Create users table if it does not exist."""

        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                role TEXT NOT NULL DEFAULT 'staff',
                is_active INTEGER NOT NULL DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        conn.commit()
        conn.close()

    def register_user(
        self,
        username: str,
        email: str,
        password: str,
        role: str = "staff"
    ) -> bool:
        """Register a new user."""

        if not username or not email or not password:
            return False

        if len(password) < 6:
            return False

        password_hash = PasswordManager.hash_password(password)

        try:
            conn = self.get_connection()
            cursor = conn.cursor()

            cursor.execute("""
                INSERT INTO users
                (username, email, password_hash, role)
                VALUES (?, ?, ?, ?)
            """, (
                username,
                email,
                password_hash,
                role
            ))

            conn.commit()
            conn.close()

            return True

        except sqlite3.IntegrityError:
            return False

        except Exception as error:
            print(f"Registration error: {error}")
            return False

    def login(
        self,
        username: str,
        password: str
    ) -> Optional[str]:
        """Authenticate user and generate session token."""

        try:
            conn = self.get_connection()
            conn.row_factory = sqlite3.Row

            cursor = conn.cursor()

            cursor.execute("""
                SELECT
                    id,
                    username,
                    email,
                    password_hash,
                    role,
                    is_active
                FROM users
                WHERE username = ?
            """, (username,))

            user = cursor.fetchone()

            conn.close()

            if not user:
                return None

            if not user["is_active"]:
                return None

            if not PasswordManager.verify_password(
                password,
                user["password_hash"]
            ):
                return None

            token = secrets.token_urlsafe(32)

            now = datetime.now()

            self.sessions[token] = {
                "user_id": user["id"],
                "username": user["username"],
                "email": user["email"],
                "role": user["role"],
                "created_at": now,
                "expires_at": now + self.SESSION_DURATION
            }

            return token

        except Exception as error:
            print(f"Login error: {error}")
            return None

    def verify_session(
        self,
        session_token: str
    ) -> Optional[Dict]:
        """Check whether a session is valid."""

        session = self.sessions.get(session_token)

        if not session:
            return None

        if datetime.now() >= session["expires_at"]:
            del self.sessions[session_token]
            return None

        return session

    def logout(self, session_token: str) -> bool:
        """Remove an active session."""

        if session_token in self.sessions:
            del self.sessions[session_token]
            return True

        return False

    def get_user(self, user_id: int) -> Optional[Dict]:
        """Get user information by ID."""

        try:
            conn = self.get_connection()
            conn.row_factory = sqlite3.Row

            cursor = conn.cursor()

            cursor.execute("""
                SELECT
                    id,
                    username,
                    email,
                    role,
                    is_active,
                    created_at
                FROM users
                WHERE id = ?
            """, (user_id,))

            user = cursor.fetchone()

            conn.close()

            if user:
                return dict(user)

            return None

        except Exception as error:
            print(f"Error getting user: {error}")
            return None

    def deactivate_user(self, user_id: int) -> bool:
        """Deactivate a user account."""

        try:
            conn = self.get_connection()
            cursor = conn.cursor()

            cursor.execute("""
                UPDATE users
                SET is_active = 0
                WHERE id = ?
            """, (user_id,))

            conn.commit()

            success = cursor.rowcount > 0

            conn.close()

            return success

        except Exception as error:
            print(f"Error deactivating user: {error}")
            return False