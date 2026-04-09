"""
database.py – SQLite connection and table creation for HealthSense.
"""

import os
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "data" / "healthsense.db"


def get_connection() -> sqlite3.Connection:
    """Return a new SQLite connection with row_factory set."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db() -> None:
    """Create all tables if they don't already exist."""
    conn = get_connection()
    cur = conn.cursor()

    cur.executescript(
        """
        CREATE TABLE IF NOT EXISTS users (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            username    TEXT    NOT NULL UNIQUE,
            password    TEXT    NOT NULL,
            created_at  TEXT    DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS profiles (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id     INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            name        TEXT    NOT NULL,
            relation    TEXT    NOT NULL DEFAULT 'Self',
            age         INTEGER,
            created_at  TEXT    DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS reports (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            profile_id  INTEGER NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
            file_path   TEXT    NOT NULL,
            report_date TEXT,
            created_at  TEXT    DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS test_results (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            report_id   INTEGER NOT NULL REFERENCES reports(id) ON DELETE CASCADE,
            test_name   TEXT    NOT NULL,
            value       TEXT,
            unit        TEXT,
            range_low   TEXT,
            range_high  TEXT,
            range_text  TEXT,
            flag        TEXT    DEFAULT 'NORMAL'
        );
        """
    )
    conn.commit()
    conn.close()
