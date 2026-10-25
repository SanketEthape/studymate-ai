
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "studymate.db"


def get_connection():
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def initialize_database():
    with get_connection() as connection:
        connection.execute("""
            CREATE TABLE IF NOT EXISTS chat_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        connection.execute("""
            CREATE TABLE IF NOT EXISTS saved_notes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                content TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        connection.execute("""
            CREATE TABLE IF NOT EXISTS study_tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task TEXT NOT NULL,
                subject TEXT DEFAULT '',
                completed INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)


def save_message(session_id, role, content):
    with get_connection() as connection:
        connection.execute(
            """
            INSERT INTO chat_history (session_id, role, content)
            VALUES (?, ?, ?)
            """,
            (session_id, role, content)
        )


def get_chat_history(session_id):
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT role, content, created_at
            FROM chat_history
            WHERE session_id = ?
            ORDER BY id
            """,
            (session_id,)
        ).fetchall()

        return [dict(row) for row in rows]


def save_note(title, content):
    with get_connection() as connection:
        connection.execute(
            "INSERT INTO saved_notes (title, content) VALUES (?, ?)",
            (title, content)
        )


def get_saved_notes():
    with get_connection() as connection:
        rows = connection.execute(
            "SELECT * FROM saved_notes ORDER BY id DESC"
        ).fetchall()

        return [dict(row) for row in rows]


def add_study_task(task, subject=""):
    with get_connection() as connection:
        connection.execute(
            "INSERT INTO study_tasks (task, subject) VALUES (?, ?)",
            (task, subject)
        )


def get_study_tasks():
    with get_connection() as connection:
        rows = connection.execute(
            "SELECT * FROM study_tasks ORDER BY id DESC"
        ).fetchall()

        return [dict(row) for row in rows]


def update_task_status(task_id, completed):
    with get_connection() as connection:
        connection.execute(
            "UPDATE study_tasks SET completed = ? WHERE id = ?",
            (int(completed), task_id)
        )
