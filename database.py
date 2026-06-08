"""
Database helper — SQLite se user aur resume data store karta hai.
Production mein PostgreSQL use kar sakte ho.
"""

import sqlite3
import json
import os
from datetime import datetime

DB_PATH = os.getenv("DB_PATH", "bot_data.db")


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Tables create karo agar exist nahi karte."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id     INTEGER PRIMARY KEY,
            first_name  TEXT,
            username    TEXT,
            plan        TEXT DEFAULT 'free',
            plan_expiry TEXT,
            created_at  TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS resumes (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id     INTEGER,
            input_data  TEXT,
            result_data TEXT,
            style       TEXT,
            created_at  TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS payments (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id     INTEGER,
            plan        TEXT,
            amount      INTEGER,
            status      TEXT DEFAULT 'pending',
            payment_id  TEXT,
            created_at  TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    conn.close()
    print("✅ Database initialized!")


def save_user(user_id: int, first_name: str, username: str):
    conn = get_connection()
    conn.execute("""
        INSERT OR IGNORE INTO users (user_id, first_name, username)
        VALUES (?, ?, ?)
    """, (user_id, first_name, username))
    conn.commit()
    conn.close()


def get_user(user_id: int):
    conn = get_connection()
    row = conn.execute(
        "SELECT * FROM users WHERE user_id = ?", (user_id,)
    ).fetchone()
    conn.close()
    return dict(row) if row else None


def get_user_plan(user_id: int) -> str:
    user = get_user(user_id)
    if not user:
        return "free"
    if user["plan"] != "free" and user["plan_expiry"]:
        expiry = datetime.fromisoformat(user["plan_expiry"])
        if datetime.now() > expiry:
            update_user_plan(user_id, "free", None)
            return "free"
    return user["plan"] or "free"


def update_user_plan(user_id: int, plan: str, expiry):
    conn = get_connection()
    conn.execute(
        "UPDATE users SET plan = ?, plan_expiry = ? WHERE user_id = ?",
        (plan, expiry, user_id)
    )
    conn.commit()
    conn.close()


def save_resume(user_id: int, input_data: dict, result_data: dict):
    conn = get_connection()
    conn.execute("""
        INSERT INTO resumes (user_id, input_data, result_data, style)
        VALUES (?, ?, ?, ?)
    """, (
        user_id,
        json.dumps(input_data, ensure_ascii=False),
        json.dumps(result_data, ensure_ascii=False),
        input_data.get("style", "modern"),
    ))
    conn.commit()
    conn.close()


def get_resume_count(user_id: int) -> int:
    conn = get_connection()
    row = conn.execute(
        "SELECT COUNT(*) as cnt FROM resumes WHERE user_id = ?",
        (user_id,)
    ).fetchone()
    conn.close()
    return row["cnt"] if row else 0


def save_payment(user_id: int, plan: str, amount: int, payment_id: str, status: str = "success"):
    conn = get_connection()
    conn.execute("""
        INSERT INTO payments (user_id, plan, amount, payment_id, status)
        VALUES (?, ?, ?, ?, ?)
    """, (user_id, plan, amount, payment_id, status))
    conn.commit()
    conn.close()


# Initialize on import
init_db()