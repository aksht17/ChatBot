import hashlib
import os
import sqlite3
import threading
import time


class IngestCache:
    def __init__(self, cache_dir):
        self.cache_dir = cache_dir
        os.makedirs(cache_dir, exist_ok=True)
        self.db_path = os.path.join(cache_dir, "ingest_cache.db")
        self._lock = threading.Lock()
        self._conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self._init_db()

    def _init_db(self):
        with self._conn:
            self._conn.execute(
                "CREATE TABLE IF NOT EXISTS file_hashes ("
                "key TEXT PRIMARY KEY, "
                "sha256 TEXT NOT NULL, "
                "updated_at REAL NOT NULL"
                ")"
            )
            self._conn.execute(
                "CREATE TABLE IF NOT EXISTS chunk_hashes ("
                "sha256 TEXT PRIMARY KEY, "
                "updated_at REAL NOT NULL"
                ")"
            )

    @staticmethod
    def hash_bytes(data):
        return hashlib.sha256(data).hexdigest()

    @staticmethod
    def hash_text(text):
        return hashlib.sha256(text.encode("utf-8", errors="ignore")).hexdigest()

    def file_unchanged(self, key, sha256):
        with self._lock:
            cur = self._conn.execute(
                "SELECT sha256 FROM file_hashes WHERE key = ?", (key,)
            )
            row = cur.fetchone()
        return row is not None and row[0] == sha256

    def update_file_hash(self, key, sha256):
        with self._lock, self._conn:
            self._conn.execute(
                "INSERT OR REPLACE INTO file_hashes (key, sha256, updated_at) "
                "VALUES (?, ?, ?)",
                (key, sha256, time.time()),
            )

    def has_chunk(self, sha256):
        with self._lock:
            cur = self._conn.execute(
                "SELECT 1 FROM chunk_hashes WHERE sha256 = ?", (sha256,)
            )
            return cur.fetchone() is not None

    def add_chunk_hashes(self, hashes):
        if not hashes:
            return
        now = time.time()
        with self._lock, self._conn:
            self._conn.executemany(
                "INSERT OR IGNORE INTO chunk_hashes (sha256, updated_at) VALUES (?, ?)",
                [(h, now) for h in hashes],
            )
