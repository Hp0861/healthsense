"""
auth.py – Simple username / password auth with bcrypt hashing.
"""

import hashlib
import hmac
import os
from typing import Optional, Tuple

from backend.database import get_connection


# ── simple SHA-256 + salt  (no external dep needed beyond stdlib) ──────────

def _hash_password(password: str) -> str:
    """Return hex-encoded salted SHA-256 hash."""
    salt = os.urandom(16).hex()
    hashed = hashlib.sha256((salt + password).encode()).hexdigest()
    return f"{salt}${hashed}"


def _verify_password(password: str, stored: str) -> bool:
    """Verify a plain-text password against the stored salt$hash."""
    try:
        salt, hashed = stored.split("$", 1)
    except ValueError:
        return False
    return hmac.compare_digest(
        hashed,
        hashlib.sha256((salt + password).encode()).hexdigest(),
    )


# ── Public API ─────────────────────────────────────────────────────────────

def register_user(username: str, password: str) -> Tuple[bool, str]:
    """
    Create a new user.
    Returns (success, message).
    """
    conn = get_connection()
    try:
        # Check uniqueness
        row = conn.execute(
            "SELECT id FROM users WHERE username = ?", (username,)
        ).fetchone()
        if row:
            return False, "Username already exists."

        hashed = _hash_password(password)
        conn.execute(
            "INSERT INTO users (username, password) VALUES (?, ?)",
            (username, hashed),
        )
        conn.commit()
        return True, "Registration successful."
    except Exception as exc:
        return False, str(exc)
    finally:
        conn.close()


def login_user(username: str, password: str) -> Tuple[bool, Optional[int], str]:
    """
    Verify credentials.
    Returns (success, user_id | None, message).
    """
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT id, password FROM users WHERE username = ?", (username,)
        ).fetchone()
        if not row:
            return False, None, "User not found."
        if not _verify_password(password, row["password"]):
            return False, None, "Invalid password."
        return True, row["id"], "Login successful."
    except Exception as exc:
        return False, None, str(exc)
    finally:
        conn.close()
