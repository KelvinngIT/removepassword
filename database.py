# database.py
import sqlite3
import hashlib
from pathlib import Path
from contextlib import contextmanager

DB_PATH = Path("users.db")


def _hash_password(password: str) -> str:
    """Simple SHA-256 hashing (you can replace with bcrypt later)."""
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


@contextmanager
def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db():
    """Create the users table if it does not exist."""
    with get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                name TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)


def user_exists(email: str) -> bool:
    email = email.strip().lower()
    with get_connection() as conn:
        row = conn.execute(
            "SELECT 1 FROM users WHERE email = ?", (email,)
        ).fetchone()
        return row is not None


def create_user(email: str, password: str, name: str) -> bool:
    """Create a new user. Returns False if email already exists."""
    email = email.strip().lower()
    try:
        with get_connection() as conn:
            conn.execute(
                "INSERT INTO users (email, password_hash, name) VALUES (?, ?, ?)",
                (email, _hash_password(password), name.strip())
            )
        return True
    except sqlite3.IntegrityError:
        return False


def set_temp_password(email: str, plain_password: str) -> bool:
    """Update the password of an existing user with a temporary one."""
    email = email.strip().lower()
    with get_connection() as conn:
        cur = conn.execute(
            "UPDATE users SET password_hash = ? WHERE email = ?",
            (_hash_password(plain_password), email)
        )
        return cur.rowcount > 0


def verify_user(email: str, password: str) -> bool:
    """Check email + password."""
    email = email.strip().lower()
    with get_connection() as conn:
        row = conn.execute(
            "SELECT password_hash FROM users WHERE email = ?", (email,)
        ).fetchone()
        if row is None:
            return False
        return row["password_hash"] == _hash_password(password)
