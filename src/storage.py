import os
import sqlite3
from datetime import datetime, timezone

DEFAULT_DB_RELATIVE = os.path.join("..", "data", "queue.db")


def get_db_path() -> str:
    env_path = os.getenv("OLLAMA_PROXY_DB")
    if env_path:
        return os.path.abspath(env_path)
    base_dir = os.path.dirname(__file__)
    return os.path.abspath(os.path.join(base_dir, DEFAULT_DB_RELATIVE))


def ensure_db_dir(db_path: str) -> None:
    os.makedirs(os.path.dirname(db_path), exist_ok=True)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def init_db() -> None:
    db_path = get_db_path()
    ensure_db_dir(db_path)
    with sqlite3.connect(db_path) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS prompts (
                id TEXT PRIMARY KEY,
                prompt TEXT NOT NULL,
                status TEXT NOT NULL,
                result TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_prompts_status_created ON prompts (status, created_at)"
        )
        conn.commit()


def open_connection() -> sqlite3.Connection:
    db_path = get_db_path()
    ensure_db_dir(db_path)
    conn = sqlite3.connect(db_path, timeout=30)
    conn.row_factory = sqlite3.Row
    return conn


def get_prompts_paginated(page: int = 1, page_size: int = 5) -> dict:
    """Get paginated list of prompts ordered by creation time (newest first)"""
    offset = (page - 1) * page_size
    with open_connection() as conn:
        # Get total count
        total = conn.execute("SELECT COUNT(*) as count FROM prompts").fetchone()["count"]
        
        # Get paginated results
        rows = conn.execute(
            """
            SELECT id, status, created_at, updated_at 
            FROM prompts 
            ORDER BY created_at DESC 
            LIMIT ? OFFSET ?
            """,
            (page_size, offset),
        ).fetchall()
        
        prompts = [dict(row) for row in rows]
        total_pages = (total + page_size - 1) // page_size if page_size > 0 else 0
        
        return {
            "prompts": prompts,
            "page": page,
            "page_size": page_size,
            "total": total,
            "total_pages": total_pages
        }
