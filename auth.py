"""
Authentication module for user management
"""
import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Optional, Dict


class PasswordManager:
    """Manage password hashing and verification"""
    
    @staticmethod
    def hash_password(password: str, salt: str = None) -> tuple:
        """Hash password with salt"""
        if salt is None:
            salt = secrets.token_hex(16)
        
        pwd_hash = hashlib.pbkdf2_hmac(
            'sha256',
            password.encode('utf-8'),
            salt.encode('utf-8'),
            100000
        ).hex()
        
        return f"{salt}${pwd_hash}", salt
    
    @staticmethod
    def verify_password(password: str, stored_hash: str) -> bool:
        """Verify password against stored hash"""
        try:
            salt = stored_hash.split('$')[0]
            pwd_hash, _ = PasswordManager.hash_password(password, salt)
            return pwd_hash == stored_hash
        except Exception:
            return False


class AuthManager:
    """Manage user authentication and sessions"""
    
    def __init__(self, db=None):
        self.db = db
        self.sessions = {}  # In-memory session storage
        self.init_auth_table()
    
    def init_auth_table(self):
        """Initialize authentication table if using database"""
        if self.db:
            conn = self.db.db_name
            import sqlite3
            conn = sqlite3.connect(conn)
            cursor = conn.cursor()
            
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    email TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    role TEXT DEFAULT 'staff',
                    is_active BOOLEAN DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            
            conn.commit()
            conn.close()
    
    def register_user(self, username: str, email: str, password: str, role: str = "staff") -> bool:
        """Register a new user"""
        try:
            if self.db:
                pwd_hash, _ = PasswordManager.hash_password(password)
                
                import sqlite3
                conn = sqlite3.connect(self.db.db_name)
                cursor = conn.cursor()
                
                cursor.execute(
                    """
                    INSERT INTO users 
                    (username, email, password_hash, role)
                    VALUES (?, ?, ?, ?)
                    """,
                    (username, email, pwd_hash, role)
                )
                
                conn.commit()
                conn.close()
                return True
        except Exception as e:
            print(f"Error registering user: {e}")
            return False
    
    def login(self, username: str, password: str) -> Optional[str]:
        """Authenticate user and create session"""
        try:
            if self.db:
                import sqlite3
                conn = sqlite3.connect(self.db.db_name)
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                cursor.execute(
                    "SELECT * FROM users WHERE username = ? AND is_active = 1",
                    (username,)
                )
                
                user = cursor.fetchone()
                conn.close()
                
                if user and PasswordManager.verify_password(password, user["password_hash"]):
                    # Create session token
                    session_token = secrets.token_urlsafe(32)
                    self.sessions[session_token] = {
                        "user_id": user["id"],
                        "username": user["username"],
                        "role": user["role"],
                        "created_at": datetime.now(),
                        "expires_at": datetime.now() + timedelta(hours=24)
                    }
                    return session_token
        except Exception as e:
            print(f"Error logging in: {e}")
        
        return None
    
    def verify_session(self, session_token: str) -> Optional[Dict]:
        """Verify session token is valid"""
        if session_token in self.sessions:
            session = self.sessions[session_token]
            if datetime.now() < session["expires_at"]:
                return session
            else:
                del self.sessions[session_token]
        return None
    
    def logout(self, session_token: str) -> bool:
        """Logout user by removing session"""
        if session_token in self.sessions:
            del self.sessions[session_token]
            return True
        return False
