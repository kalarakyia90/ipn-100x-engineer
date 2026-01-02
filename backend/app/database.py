"""
Database connection and initialization for SQLite.

Uses a context manager pattern to ensure connections are properly
closed after each request, preventing connection leaks.
"""

import sqlite3
from pathlib import Path
from contextlib import contextmanager
from typing import Generator

# Database path - stored in backend/data/
DB_PATH = Path(__file__).parent.parent / "data" / "restaurant.db"


def get_db_connection() -> sqlite3.Connection:
    """Create a database connection with row factory for dict-like access."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


@contextmanager
def get_db() -> Generator[sqlite3.Connection, None, None]:
    """
    Context manager for database connections.

    Automatically commits on success, rolls back on error,
    and always closes the connection.
    """
    conn = get_db_connection()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_database() -> None:
    """
    Initialize database tables and indexes.

    Uses IF NOT EXISTS to make this idempotent - safe to call
    multiple times without dropping existing data.
    """
    with get_db() as conn:
        cursor = conn.cursor()

        # Reservations table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS reservations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                restaurant_id TEXT NOT NULL,
                customer_name TEXT NOT NULL,
                customer_email TEXT NOT NULL,
                customer_phone TEXT,
                party_size INTEGER NOT NULL,
                reservation_date TEXT NOT NULL,
                reservation_time TEXT NOT NULL,
                status TEXT DEFAULT 'pending',
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Reviews table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS reviews (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                restaurant_id TEXT NOT NULL,
                reviewer_name TEXT NOT NULL,
                reviewer_email TEXT,
                rating INTEGER NOT NULL CHECK (rating >= 1 AND rating <= 5),
                title TEXT,
                comment TEXT,
                visit_date TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Indexes for common query patterns
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_reservations_restaurant "
            "ON reservations(restaurant_id)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_reservations_date "
            "ON reservations(reservation_date)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_reviews_restaurant "
            "ON reviews(restaurant_id)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_reviews_rating "
            "ON reviews(rating)"
        )

        print("Database initialized successfully!")
