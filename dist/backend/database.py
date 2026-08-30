"""
ADIS SQLite Database Persistence Layer
Stores forensic analysis records in adis_forensics.db for multi-investigator case collaboration.
"""

from pathlib import Path
import sqlite3
import json
from datetime import datetime, timezone

DB_PATH = Path(__file__).resolve().parent / "adis_forensics.db"


def get_connection():
    """Create a thread-safe connection to adis_forensics.db."""
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Initialize database tables if they do not exist."""
    conn = get_connection()
    try:
        with conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS analyses (
                    id TEXT PRIMARY KEY,
                    analysis_id TEXT UNIQUE,
                    media_type TEXT NOT NULL,
                    filename TEXT NOT NULL,
                    sha256 TEXT,
                    file_size_bytes INTEGER,
                    classification TEXT NOT NULL,
                    confidence REAL NOT NULL,
                    processing_time_ms INTEGER,
                    model_name TEXT,
                    model_version TEXT,
                    timestamp TEXT NOT NULL,
                    simulated INTEGER DEFAULT 0,
                    payload_json TEXT
                )
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_media_type ON analyses(media_type)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_timestamp ON analyses(timestamp DESC)")
        print(f"[Database] SQLite database initialized at {DB_PATH}")
    finally:
        conn.close()


def save_analysis(record: dict) -> dict:
    """
    Save or update a forensic analysis record in SQLite.
    Expects standardized or legacy envelope result dict.
    """
    conn = get_connection()
    try:
        analysis_id = record.get("analysis_id") or record.get("id") or f"ANALYSIS-{int(datetime.now().timestamp())}"
        media_type = record.get("media_type") or record.get("type") or "unknown"
        filename = record.get("filename") or record.get("evidence", {}).get("filename") or "evidence_file"
        sha256 = record.get("sha256") or record.get("evidence", {}).get("sha256")
        file_size_bytes = record.get("file_size_bytes") or record.get("evidence", {}).get("file_size_bytes", 0)
        classification = record.get("classification") or record.get("analysis", {}).get("classification") or "INCONCLUSIVE"
        confidence = float(record.get("confidence") or record.get("analysis", {}).get("confidence", 0.0))
        processing_time_ms = int(record.get("processing", {}).get("processing_time_ms") or record.get("processing_time_ms", 0))
        model_name = record.get("model", {}).get("name") if isinstance(record.get("model"), dict) else record.get("model") or "ADIS-Detector"
        model_version = record.get("model", {}).get("version") if isinstance(record.get("model"), dict) else record.get("model_version") or "1.0.0"
        timestamp = record.get("timestamp") or datetime.now(timezone.utc).isoformat()
        simulated = 1 if record.get("_simulated") or record.get("simulated") else 0
        payload_json = json.dumps(record)

        with conn:
            conn.execute("""
                INSERT OR REPLACE INTO analyses (
                    id, analysis_id, media_type, filename, sha256, file_size_bytes,
                    classification, confidence, processing_time_ms, model_name,
                    model_version, timestamp, simulated, payload_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                analysis_id, analysis_id, media_type, filename, sha256, file_size_bytes,
                classification, confidence, processing_time_ms, model_name,
                model_version, timestamp, simulated, payload_json
            ))

        return {
            "id": analysis_id,
            "analysis_id": analysis_id,
            "media_type": media_type,
            "filename": filename,
            "sha256": sha256,
            "file_size_bytes": file_size_bytes,
            "classification": classification,
            "confidence": confidence,
            "processing_time_ms": processing_time_ms,
            "model_name": model_name,
            "timestamp": timestamp,
            "simulated": bool(simulated)
        }
    finally:
        conn.close()


def get_history(limit: int = 200) -> list:
    """Retrieve history records from SQLite database, newest first."""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, analysis_id, media_type, filename, sha256, file_size_bytes,
                   classification, confidence, processing_time_ms, model_name,
                   model_version, timestamp, simulated, payload_json
            FROM analyses
            ORDER BY timestamp DESC
            LIMIT ?
        """, (limit,))

        rows = cursor.fetchall()
        results = []
        for r in rows:
            record = dict(r)
            if record.get("payload_json"):
                try:
                    payload = json.loads(record["payload_json"])
                    payload["type"] = record["media_type"]
                    payload["confidence"] = record["confidence"] if record["confidence"] > 1.0 else round(record["confidence"] * 100, 1)
                    results.append(payload)
                    continue
                except Exception:
                    pass
            results.append({
                "id": record["id"],
                "type": record["media_type"],
                "filename": record["filename"],
                "verdict": record["classification"],
                "confidence": record["confidence"] if record["confidence"] > 1.0 else round(record["confidence"] * 100, 1),
                "sha256": record["sha256"],
                "model": record["model_name"],
                "timestamp": record["timestamp"],
                "simulated": bool(record["simulated"])
            })
        return results
    finally:
        conn.close()


def clear_history():
    """Clear all records from analyses table."""
    conn = get_connection()
    try:
        with conn:
            conn.execute("DELETE FROM analyses")
    finally:
        conn.close()


# Initialize database on module import
init_db()
