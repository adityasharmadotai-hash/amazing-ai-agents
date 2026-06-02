"""SQLite storage for analyzed emails."""
import sqlite3
from contextlib import contextmanager
from datetime import datetime

DB_PATH = "email_agent.db"


@contextmanager
def _conn(db_path: str = DB_PATH):
    """Open a connection and always close it, even on error."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db(db_path: str = DB_PATH) -> None:
    """Create the table on first run."""
    with _conn(db_path) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS emails (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                email_id    TEXT UNIQUE,          -- Gmail message id (dedupe key)
                date        TEXT,
                sender      TEXT,
                subject     TEXT,
                summary     TEXT,
                action_item TEXT,
                priority    TEXT,                 -- High / Medium / Low
                due_date    TEXT,
                status      TEXT DEFAULT 'Pending',
                created_at  TEXT
            )
            """
        )


def already_processed(email_id: str, db_path: str = DB_PATH) -> bool:
    """True if we have already analyzed this Gmail message."""
    with _conn(db_path) as conn:
        row = conn.execute(
            "SELECT 1 FROM emails WHERE email_id = ?", (email_id,)
        ).fetchone()
        return row is not None


def save_email(record: dict, db_path: str = DB_PATH) -> None:
    """Insert one analyzed email. Ignores duplicates."""
    with _conn(db_path) as conn:
        conn.execute(
            """
            INSERT OR IGNORE INTO emails
            (email_id, date, sender, subject, summary, action_item,
             priority, due_date, status, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                record.get("email_id"),
                record.get("date"),
                record.get("sender"),
                record.get("subject"),
                record.get("summary"),
                record.get("action_item"),
                record.get("priority"),
                record.get("due_date"),
                record.get("status", "Pending"),
                datetime.utcnow().isoformat(),
            ),
        )


def get_all_emails(db_path: str = DB_PATH) -> list[dict]:
    """Return every stored email, newest first."""
    with _conn(db_path) as conn:
        rows = conn.execute(
            "SELECT * FROM emails ORDER BY created_at DESC"
        ).fetchall()
        return [dict(r) for r in rows]


def update_status(row_id: int, status: str, db_path: str = DB_PATH) -> None:
    """Flip an email between Pending and Completed."""
    with _conn(db_path) as conn:
        conn.execute(
            "UPDATE emails SET status = ? WHERE id = ?", (status, row_id)
        )
