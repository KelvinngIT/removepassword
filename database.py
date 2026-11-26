import sqlite3
import bcrypt
from pathlib import Path

DB_PATH = Path("users.db")

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            name TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

def create_user(email: str, password: str, name: str = "") -> bool:
    try:
        password_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt())
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute(
            "INSERT INTO users (email, password_hash, name) VALUES (?, ?, ?)",
            (email.lower().strip(), password_hash, name)
        )
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        return False

def verify_user(email: str, password: str) -> bool:
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT password_hash FROM users WHERE email = ?", (email.lower().strip(),))
    row = c.fetchone()
    conn.close()

    if row is None:
        return False
    return bcrypt.checkpw(password.encode(), row[0])

def get_user_name(email: str) -> str:
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT name FROM users WHERE email = ?", (email.lower().strip(),))
    row = c.fetchone()
    conn.close()
    return row[0] if row else ""
