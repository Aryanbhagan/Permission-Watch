
import sqlite3
from pathlib import Path
from datetime import datetime

DB_PATH = Path(__file__).parent / "permission_watch.db"


def initialize_database():
    """Create the events table if it does not exist."""
    with sqlite3.connect(DB_PATH) as connection:
        connection.execute("""
            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                event_type TEXT NOT NULL,
                file_path TEXT NOT NULL,
                old_value TEXT,
                new_value TEXT,
                risk_level TEXT
            )
        """)

    print(f"Database ready: {DB_PATH}")


def log_event(event_type, file_path, old_value=None,
              new_value=None, risk_level="INFO"):
    """Store a monitoring event in SQLite."""
    timestamp = datetime.now().astimezone().isoformat(
        timespec="seconds"
    )

    with sqlite3.connect(DB_PATH) as connection:
        connection.execute("""
            INSERT INTO events (
                timestamp, event_type, file_path,
                old_value, new_value, risk_level
            )
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            timestamp,
            event_type,
            str(file_path),
            str(old_value) if old_value is not None else None,
            str(new_value) if new_value is not None else None,
            risk_level
        ))


def get_recent_events(limit=20):
    """Return the latest events, newest first."""
    with sqlite3.connect(DB_PATH) as connection:
        return connection.execute("""
            SELECT id, timestamp, event_type, file_path,
                   old_value, new_value, risk_level
            FROM events
            ORDER BY id DESC
            LIMIT ?
        """, (limit,)).fetchall()


if __name__ == "__main__":
    initialize_database()

    log_event(
        event_type="TEST_EVENT",
        file_path="test_data/example.txt",
        old_value="644",
        new_value="777",
        risk_level="HIGH"
    )

    print("\nLatest database events:")
    for event in get_recent_events():
        print(event)
