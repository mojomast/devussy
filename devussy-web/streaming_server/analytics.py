import os
import hashlib
import json
import time
import sqlite3
from typing import Optional, Dict, Any

DB_PATH = os.getenv('DEVUSSY_ANALYTICS_DB', 'analytics.db')


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_connection()
    with conn:
        conn.executescript('''
        CREATE TABLE IF NOT EXISTS sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT UNIQUE NOT NULL,
            ip_hash TEXT NOT NULL,
            user_agent TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS api_calls (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT,
            endpoint TEXT NOT NULL,
            method TEXT NOT NULL,
            status_code INTEGER,
            duration_ms REAL,
            request_size INTEGER,
            response_size INTEGER,
            model_used TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (session_id) REFERENCES sessions(session_id)
        );
        CREATE TABLE IF NOT EXISTS user_inputs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT,
            input_type TEXT NOT NULL,
            project_name TEXT,
            sanitized_requirements TEXT,
            languages TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (session_id) REFERENCES sessions(session_id)
        );
        ''')
    conn.close()


def hash_ip(ip: str) -> str:
    return hashlib.sha256(ip.encode('utf-8')).hexdigest()


def log_session(session_id: str, ip: str, user_agent: Optional[str] = None):
    conn = get_connection()
    with conn:
        conn.execute(
            "INSERT OR IGNORE INTO sessions (session_id, ip_hash, user_agent) VALUES (?, ?, ?)",
            (session_id, hash_ip(ip), user_agent),
        )
    conn.close()


def log_api_call(
    session_id: str,
    endpoint: str,
    method: str,
    status_code: int,
    duration_ms: float,
    request_size: int,
    response_size: int,
    model_used: Optional[str] = None,
):
    conn = get_connection()
    with conn:
        conn.execute(
            "INSERT INTO api_calls (session_id, endpoint, method, status_code, duration_ms, request_size, response_size, model_used) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (
                session_id,
                endpoint,
                method,
                status_code,
                duration_ms,
                request_size,
                response_size,
                model_used,
            ),
        )
    conn.close()


def sanitize_requirements(req: str) -> str:
    # Simple redaction: remove any API keys or tokens patterns
    # This is a placeholder; real implementation would use regexes for common patterns
    return req.replace('API_KEY', '[REDACTED]').replace('TOKEN', '[REDACTED]')


def log_user_input(
    session_id: str,
    input_type: str,
    project_name: Optional[str] = None,
    requirements: Optional[str] = None,
    languages: Optional[str] = None,
):
    # Normalize languages to a string for SQLite storage
    if languages is None:
        normalized_languages = None
    elif isinstance(languages, (list, tuple, set)):
        try:
            normalized_languages = ", ".join(str(lang) for lang in languages)
        except Exception:
            normalized_languages = str(languages)
    else:
        normalized_languages = str(languages)

    conn = get_connection()
    with conn:
        conn.execute(
            "INSERT INTO user_inputs (session_id, input_type, project_name, sanitized_requirements, languages) VALUES (?, ?, ?, ?, ?)",
            (
                session_id,
                input_type,
                project_name,
                sanitize_requirements(requirements or ''),
                normalized_languages,
            ),
        )
    conn.close()


def get_overview() -> Dict[str, Any]:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute('SELECT COUNT(*) FROM sessions')
    total_sessions = cur.fetchone()[0]
    cur.execute('SELECT COUNT(*) FROM api_calls')
    total_calls = cur.fetchone()[0]
    cur.execute('SELECT endpoint, COUNT(*) as cnt FROM api_calls GROUP BY endpoint ORDER BY cnt DESC LIMIT 5')
    popular = [{"endpoint": row[0], "count": row[1]} for row in cur.fetchall()]
    cur.execute('SELECT AVG(duration_ms) FROM api_calls')
    avg_latency = cur.fetchone()[0]
    cur.execute('SELECT model_used, COUNT(*) FROM api_calls WHERE model_used IS NOT NULL GROUP BY model_used')
    model_usage = [{"model": row[0], "count": row[1]} for row in cur.fetchall()]
    conn.close()
    return {
        "total_sessions": total_sessions,
        "total_api_calls": total_calls,
        "popular_endpoints": popular,
        "average_latency_ms": avg_latency,
        "model_usage": model_usage,
    }
