"""Local SQLite and file cache engine for financial data tools.

Prevents redundant network calls to SEC EDGAR and transcript providers by caching
HTTP responses and parsed documents locally in SQLite.
"""

import os
import sqlite3
import time
import logging
from pathlib import Path
from typing import Optional, Dict, Any

logger = logging.getLogger("financial_agent.cache")


class LocalCache:
    """SQLite-backed key-value cache with TTL expiration support."""

    def __init__(self, db_path: Optional[str] = None) -> None:
        if db_path is None:
            db_dir = Path("./cache")
            db_dir.mkdir(parents=True, exist_ok=True)
            db_path = str(db_dir / "http_cache.db")

        self.db_path = db_path
        self._init_db()

    def _init_db(self) -> None:
        """Initialize SQLite cache table schema."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS response_cache (
                        key TEXT PRIMARY KEY,
                        value TEXT NOT NULL,
                        created_at REAL NOT NULL,
                        expires_at REAL
                    )
                """)
                conn.commit()
        except Exception as err:
            logger.warning(f"Failed to initialize SQLite cache at {self.db_path}: {err}")

    def get(self, key: str) -> Optional[str]:
        """Retrieve cached string value if key exists and is not expired."""
        try:
            now = time.time()
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT value, expires_at FROM response_cache WHERE key = ?",
                    (key,)
                )
                row = cursor.fetchone()
                if not row:
                    return None

                value, expires_at = row
                if expires_at is not None and now > expires_at:
                    cursor.execute("DELETE FROM response_cache WHERE key = ?", (key,))
                    conn.commit()
                    return None

                return value
        except Exception as err:
            logger.warning(f"Cache lookup error for key '{key}': {err}")
            return None

    def set(self, key: str, value: str, ttl_seconds: Optional[int] = 86400 * 7) -> None:
        """Store string value in cache with optional TTL (default 7 days)."""
        try:
            now = time.time()
            expires_at = (now + ttl_seconds) if ttl_seconds else None
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO response_cache (key, value, created_at, expires_at)
                    VALUES (?, ?, ?, ?)
                """, (key, value, now, expires_at))
                conn.commit()
        except Exception as err:
            logger.warning(f"Cache write error for key '{key}': {err}")

    def clear(self) -> None:
        """Clear all entries in the cache."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("DELETE FROM response_cache")
                conn.commit()
        except Exception as err:
            logger.warning(f"Cache clear error: {err}")


# Global default cache instance
default_cache = LocalCache()
