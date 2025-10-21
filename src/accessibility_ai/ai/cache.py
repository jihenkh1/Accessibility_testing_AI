import json
import sqlite3
import hashlib
import logging
from pathlib import Path
from typing import Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class AICache:
    """
    SQLite-backed cache for AI enrichment results with expiration support.
    
    Features:
    - Automatic expiration of old entries
    - Cleanup of stale data
    - Thread-safe operations
    """

    def __init__(self, db_path: Path, ttl_days: int = 30) -> None:
        """
        Initialize cache with expiration support.
        
        Args:
            db_path: Path to SQLite database file
            ttl_days: Time-to-live in days (default: 30 days)
        """
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.ttl_days = ttl_days
        self._ensure()

    def _ensure(self) -> None:
        """Create cache table with expiration tracking and handle migrations."""
        conn = sqlite3.connect(self.db_path)
        try:
            # Create table with created_at and expires_at columns
            conn.execute(
                """CREATE TABLE IF NOT EXISTS cache (
                    key TEXT PRIMARY KEY, 
                    value TEXT NOT NULL, 
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    expires_at DATETIME NOT NULL
                )"""
            )
            
            # Check if we need to migrate old schema (without expires_at)
            cur = conn.execute("PRAGMA table_info(cache)")
            columns = [row[1] for row in cur.fetchall()]
            
            if 'expires_at' not in columns:
                logger.warning("Migrating cache schema: adding expires_at column")
                # Add expires_at column with default value (30 days from now)
                default_expiry = (datetime.now() + timedelta(days=self.ttl_days)).isoformat()
                conn.execute(
                    f"ALTER TABLE cache ADD COLUMN expires_at DATETIME DEFAULT '{default_expiry}'"
                )
                # Update all existing rows to have an expiration date
                conn.execute(
                    f"UPDATE cache SET expires_at = '{default_expiry}' WHERE expires_at IS NULL"
                )
                conn.commit()
                logger.info("Cache schema migration completed")
            
            # Create index on expires_at for efficient cleanup
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_expires_at ON cache(expires_at)"
            )
            conn.commit()
            logger.info(f"Cache initialized at {self.db_path} (TTL: {self.ttl_days} days)")
        except Exception as e:
            logger.error(f"Failed to initialize cache: {e}")
            raise
        finally:
            conn.close()

    @staticmethod
    def make_key(*parts: object) -> str:
        payload = json.dumps(parts, ensure_ascii=False, sort_keys=True, default=str)
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

    def get(self, key: str) -> Optional[str]:
        """
        Get cached value if it exists and hasn't expired.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None if not found or expired
        """
        conn = sqlite3.connect(self.db_path)
        try:
            cur = conn.execute(
                "SELECT value FROM cache WHERE key = ? AND expires_at > CURRENT_TIMESTAMP", 
                (key,)
            )
            row = cur.fetchone()
            if row:
                logger.debug(f"Cache HIT for key {key[:16]}...")
                return row[0]
            else:
                logger.debug(f"Cache MISS for key {key[:16]}...")
                return None
        finally:
            conn.close()

    def set(self, key: str, value: str) -> None:
        """
        Store value in cache with automatic expiration.
        
        Args:
            key: Cache key
            value: Value to cache (must be string/JSON)
        """
        conn = sqlite3.connect(self.db_path)
        try:
            # Calculate expiration date
            expires_at = (datetime.now() + timedelta(days=self.ttl_days)).isoformat()
            
            conn.execute(
                "INSERT OR REPLACE INTO cache(key, value, expires_at) VALUES(?, ?, ?)", 
                (key, value, expires_at)
            )
            conn.commit()
            logger.debug(f"Cache SET for key {key[:16]}... (expires: {expires_at})")
        finally:
            conn.close()
    
    def cleanup_expired(self) -> int:
        """
        Remove all expired entries from cache.
        
        Returns:
            Number of entries removed
        """
        conn = sqlite3.connect(self.db_path)
        try:
            cur = conn.execute(
                "DELETE FROM cache WHERE expires_at <= CURRENT_TIMESTAMP"
            )
            deleted = cur.rowcount
            conn.commit()
            if deleted > 0:
                logger.info(f"Cleaned up {deleted} expired cache entries")
            return deleted
        finally:
            conn.close()
    
    def get_stats(self) -> dict:
        """
        Get cache statistics.
        
        Returns:
            Dictionary with cache metrics
        """
        conn = sqlite3.connect(self.db_path)
        try:
            # Count total entries
            cur = conn.execute("SELECT COUNT(*) FROM cache")
            total = cur.fetchone()[0]
            
            # Count expired entries
            cur = conn.execute("SELECT COUNT(*) FROM cache WHERE expires_at <= CURRENT_TIMESTAMP")
            expired = cur.fetchone()[0]
            
            # Count valid entries
            valid = total - expired
            
            # Get oldest and newest entries
            cur = conn.execute("SELECT MIN(created_at), MAX(created_at) FROM cache WHERE expires_at > CURRENT_TIMESTAMP")
            row = cur.fetchone()
            oldest, newest = row[0], row[1]
            
            return {
                "total_entries": total,
                "valid_entries": valid,
                "expired_entries": expired,
                "oldest_entry": oldest,
                "newest_entry": newest,
                "ttl_days": self.ttl_days
            }
        finally:
            conn.close()
    
    def clear_all(self) -> int:
        """
        Clear all cache entries (use with caution!).
        
        Returns:
            Number of entries removed
        """
        conn = sqlite3.connect(self.db_path)
        try:
            cur = conn.execute("DELETE FROM cache")
            deleted = cur.rowcount
            conn.commit()
            logger.warning(f"Cleared entire cache ({deleted} entries removed)")
            return deleted
        finally:
            conn.close()

