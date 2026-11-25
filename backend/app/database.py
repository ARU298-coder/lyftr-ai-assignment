import os
import json
import sqlite3
from datetime import datetime, timezone

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./app.db")
DB_PATH = DATABASE_URL.replace("sqlite:///", "", 1)


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_connection()

    conn.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            metadata TEXT,
            created_at TEXT NOT NULL
        )
    """)

    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_messages_session
        ON messages(session_id, id)
    """)

    conn.commit()
    conn.close()


def save_message(session_id, role, content, metadata=None):
    conn = get_connection()

    metadata_json = json.dumps(metadata) if metadata else None

    conn.execute(
        """
        INSERT INTO messages
        (session_id, role, content, metadata, created_at)
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            session_id,
            role,
            content,
            metadata_json,
            datetime.now(timezone.utc).isoformat()
        )
    )

    conn.commit()
    conn.close()


def get_messages(session_id):
    conn = get_connection()

    rows = conn.execute(
        """
        SELECT role, content, metadata
        FROM messages
        WHERE session_id = ?
        ORDER BY id ASC
        """,
        (session_id,)
    ).fetchall()

    conn.close()

    result = []

    for row in rows:
        message = {
            "role": row["role"],
            "content": row["content"]
        }

        if row["metadata"]:
            message["metadata"] = json.loads(row["metadata"])

        result.append(message)

    return result