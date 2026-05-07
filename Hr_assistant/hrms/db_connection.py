"""
db_connection.py
────────────────
Central MySQL connection helper for the HRMS app.
All manager classes import get_connection() from here.

Setup:
    pip install mysql-connector-python

Edit the CONFIG dict below to match your MySQL credentials.
"""

import mysql.connector
from mysql.connector import Error
from contextlib import contextmanager

# ── Edit these to match your MySQL setup ─────────────────────────────────────
CONFIG = {
    "host":     "localhost",
    "port":     3306,
    "user":     "root",
    "password": "manoj123",   # <-- change this
    "database": "hr_management",
    "charset":  "utf8mb4",
}

def get_connection():
    """Return a new MySQL connection. Caller is responsible for closing it."""
    try:
        conn = mysql.connector.connect(**CONFIG)
        return conn
    except Error as e:
        raise ConnectionError(f"Could not connect to MySQL: {e}")


@contextmanager
def db_cursor(dictionary: bool = True):
    """
    Context manager that yields a cursor and auto-commits / rolls back.

    Usage:
        with db_cursor() as cur:
            cur.execute("SELECT ...")
            rows = cur.fetchall()
    """
    conn = get_connection()
    cursor = conn.cursor(dictionary=dictionary)
    try:
        yield cursor
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()


def test_connection() -> str:
    """Quick check — returns a success/failure message."""
    try:
        with db_cursor() as cur:
            cur.execute("SELECT COUNT(*) AS total FROM employees")
            row = cur.fetchone()
        return f"Connected! hr_management has {row['total']} employees."
    except Exception as e:
        return f"Connection failed: {e}"


if __name__ == "__main__":
    print(test_connection())
