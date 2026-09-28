"""
ADIS SQLite Database Persistence Layer
Stores forensic analysis records, cases, and evidence in adis_forensics.db
for multi-investigator digital forensic collaboration.
"""

from pathlib import Path
import sqlite3
import json
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any

DB_PATH = Path(__file__).resolve().parent / "adis_forensics.db"


def get_connection():
    """Create a thread-safe connection to adis_forensics.db."""
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Initialize database tables and seed defaults if they do not exist."""
    conn = get_connection()
    try:
        with conn:
            # 1. Analyses Table (History & Logs)
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

            # 2. Cases Table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS cases (
                    id TEXT PRIMARY KEY,
                    case_number TEXT UNIQUE,
                    title TEXT NOT NULL,
                    description TEXT,
                    investigator TEXT NOT NULL DEFAULT 'Active Investigator',
                    priority TEXT NOT NULL DEFAULT 'MEDIUM',
                    status TEXT NOT NULL DEFAULT 'ACTIVE',
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    metadata_json TEXT
                )
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_case_status ON cases(status)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_case_updated ON cases(updated_at DESC)")

            # 3. Evidence Table (Associated with Cases)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS evidence (
                    id TEXT PRIMARY KEY,
                    case_id TEXT NOT NULL,
                    media_type TEXT NOT NULL,
                    filename TEXT NOT NULL,
                    sha256 TEXT,
                    file_size_bytes INTEGER,
                    analysis_id TEXT,
                    verdict TEXT DEFAULT 'INCONCLUSIVE',
                    confidence REAL DEFAULT 0.0,
                    uploaded_at TEXT NOT NULL,
                    metadata_json TEXT,
                    FOREIGN KEY(case_id) REFERENCES cases(id) ON DELETE CASCADE
                )
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_evidence_case ON evidence(case_id)")

            # 4. Seed default investigation cases if table is empty
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) as cnt FROM cases")
            if cursor.fetchone()["cnt"] == 0:
                now_iso = datetime.now(timezone.utc).isoformat()
                seed_cases = [
                    (
                        "CAS-4492",
                        "#4492",
                        "Operation Silk Road Data Extraction",
                        "Multi-modal investigation of suspected synthetic press release assets and audio clips.",
                        "J. Doe",
                        "HIGH",
                        "ACTIVE",
                        "2023-10-24T10:00:00Z",
                        now_iso,
                        json.dumps({"tags": ["synthetic-media", "press-briefing", "priority-alpha"]})
                    ),
                    (
                        "CAS-4491",
                        "#4491",
                        "Financial Fraud - Enron Archives",
                        "Audit of legacy audio recordings and scanned evidentiary documents.",
                        "A. Smith",
                        "MEDIUM",
                        "UNDER_REVIEW",
                        "2023-10-22T14:30:00Z",
                        now_iso,
                        json.dumps({"tags": ["financial", "audio-tampering"]})
                    ),
                    (
                        "CAS-2026-081",
                        "#2026-081",
                        "Suspected Executive Voice Clone",
                        "Forensic spectrogram analysis of spear-phishing voicemail purporting to be CEO.",
                        "Active Investigator",
                        "HIGH",
                        "ACTIVE",
                        now_iso,
                        now_iso,
                        json.dumps({"tags": ["voice-clone", "yamnet", "urgent"]})
                    ),
                ]
                conn.executemany("""
                    INSERT INTO cases (
                        id, case_number, title, description, investigator,
                        priority, status, created_at, updated_at, metadata_json
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, seed_cases)

        print(f"[Database] SQLite database initialized with Cases & Evidence tables at {DB_PATH}")
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# 1. ANALYSIS PERSISTENCE & HISTORY
# ---------------------------------------------------------------------------

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
        sha256 = record.get("sha256") or record.get("evidence", {}).get("sha256") or ""
        file_size_bytes = record.get("file_size_bytes") or record.get("evidence", {}).get("file_size_bytes", 0)
        classification = record.get("classification") or record.get("analysis", {}).get("classification") or "INCONCLUSIVE"
        
        raw_conf = record.get("confidence") or record.get("analysis", {}).get("confidence", 0.0)
        confidence = float(raw_conf) if float(raw_conf) <= 1.0 else float(raw_conf) / 100.0

        proc_ms = record.get("processing", {}).get("processing_time_ms") or record.get("processing_time_ms", 0)
        processing_time_ms = int(proc_ms)

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


def clear_history() -> int:
    """Clear all records from analyses table."""
    conn = get_connection()
    try:
        with conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM analyses")
            return cursor.rowcount
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# 2. CASE MANAGEMENT CRUD
# ---------------------------------------------------------------------------

def create_case(case_data: dict) -> dict:
    """Create a new forensic investigation case."""
    conn = get_connection()
    try:
        now_iso = datetime.now(timezone.utc).isoformat()
        case_id = case_data.get("id") or f"CAS-{int(datetime.now().timestamp())}"
        case_number = case_data.get("case_number") or f"#{case_id.replace('CAS-', '')}"
        title = case_data.get("title", "Untitled Forensic Investigation")
        description = case_data.get("description", "")
        investigator = case_data.get("investigator", "Active Investigator")
        priority = (case_data.get("priority") or "MEDIUM").upper()
        status = (case_data.get("status") or "ACTIVE").upper()
        metadata_json = json.dumps(case_data.get("metadata", {}))

        with conn:
            conn.execute("""
                INSERT INTO cases (
                    id, case_number, title, description, investigator,
                    priority, status, created_at, updated_at, metadata_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                case_id, case_number, title, description, investigator,
                priority, status, now_iso, now_iso, metadata_json
            ))

        return get_case(case_id)
    finally:
        conn.close()


def get_cases(status: Optional[str] = None, priority: Optional[str] = None, limit: int = 100) -> List[dict]:
    """Retrieve list of cases with associated evidence counts."""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        query = """
            SELECT c.*, 
                   (SELECT COUNT(*) FROM evidence e WHERE e.case_id = c.id) as evidence_count
            FROM cases c
            WHERE 1=1
        """
        params = []
        if status and status.upper() != "ALL":
            query += " AND UPPER(c.status) = ?"
            params.append(status.upper())
        if priority and priority.upper() != "ALL":
            query += " AND UPPER(c.priority) = ?"
            params.append(priority.upper())

        query += " ORDER BY c.updated_at DESC LIMIT ?"
        params.append(limit)

        cursor.execute(query, tuple(params))
        rows = cursor.fetchall()
        cases = []
        for r in rows:
            cd = dict(r)
            if cd.get("metadata_json"):
                try:
                    cd["metadata"] = json.loads(cd["metadata_json"])
                except Exception:
                    cd["metadata"] = {}
            cases.append(cd)
        return cases
    finally:
        conn.close()


def get_case(case_id: str) -> Optional[dict]:
    """Retrieve full details of a specific case, including its attached evidence."""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM cases WHERE id = ? OR case_number = ?", (case_id, case_id))
        row = cursor.fetchone()
        if not row:
            return None

        case_dict = dict(row)
        if case_dict.get("metadata_json"):
            try:
                case_dict["metadata"] = json.loads(case_dict["metadata_json"])
            except Exception:
                case_dict["metadata"] = {}

        # Fetch attached evidence items
        cursor.execute("""
            SELECT * FROM evidence WHERE case_id = ? ORDER BY uploaded_at DESC
        """, (case_dict["id"],))
        evidence_rows = cursor.fetchall()
        case_dict["evidence"] = [dict(e) for e in evidence_rows]
        case_dict["evidence_count"] = len(case_dict["evidence"])

        return case_dict
    finally:
        conn.close()


def update_case(case_id: str, updates: dict) -> Optional[dict]:
    """Update fields of an existing case."""
    conn = get_connection()
    try:
        now_iso = datetime.now(timezone.utc).isoformat()
        fields = []
        params = []

        for k in ["title", "description", "investigator", "priority", "status"]:
            if k in updates:
                fields.append(f"{k} = ?")
                params.append(updates[k].upper() if k in ["priority", "status"] else updates[k])

        if "metadata" in updates:
            fields.append("metadata_json = ?")
            params.append(json.dumps(updates["metadata"]))

        if not fields:
            return get_case(case_id)

        fields.append("updated_at = ?")
        params.append(now_iso)

        params.append(case_id)
        params.append(case_id)

        with conn:
            conn.execute(f"""
                UPDATE cases SET {', '.join(fields)}
                WHERE id = ? OR case_number = ?
            """, tuple(params))

        return get_case(case_id)
    finally:
        conn.close()


def delete_case(case_id: str) -> bool:
    """Delete a case and all attached evidence items."""
    conn = get_connection()
    try:
        with conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM evidence WHERE case_id = ?", (case_id,))
            cursor.execute("DELETE FROM cases WHERE id = ? OR case_number = ?", (case_id, case_id))
            return cursor.rowcount > 0
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# 3. EVIDENCE LINKING
# ---------------------------------------------------------------------------

def add_evidence_to_case(case_id: str, evidence_data: dict) -> dict:
    """Attach an analyzed piece of forensic evidence to an investigation case."""
    conn = get_connection()
    try:
        now_iso = datetime.now(timezone.utc).isoformat()
        evidence_id = evidence_data.get("id") or f"EVD-{int(datetime.now().timestamp())}"
        media_type = evidence_data.get("media_type") or evidence_data.get("type", "unknown")
        filename = evidence_data.get("filename", "evidence_file")
        sha256 = evidence_data.get("sha256", "")
        file_size_bytes = int(evidence_data.get("file_size_bytes", 0))
        analysis_id = evidence_data.get("analysis_id", "")
        verdict = (evidence_data.get("verdict") or evidence_data.get("classification") or "INCONCLUSIVE").upper()
        confidence = float(evidence_data.get("confidence", 0.0))
        metadata_json = json.dumps(evidence_data.get("metadata", {}))

        with conn:
            conn.execute("""
                INSERT INTO evidence (
                    id, case_id, media_type, filename, sha256, file_size_bytes,
                    analysis_id, verdict, confidence, uploaded_at, metadata_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                evidence_id, case_id, media_type, filename, sha256, file_size_bytes,
                analysis_id, verdict, confidence, now_iso, metadata_json
            ))

            # Bump case updated_at
            conn.execute("UPDATE cases SET updated_at = ? WHERE id = ?", (now_iso, case_id))

        return {
            "id": evidence_id,
            "case_id": case_id,
            "media_type": media_type,
            "filename": filename,
            "sha256": sha256,
            "file_size_bytes": file_size_bytes,
            "analysis_id": analysis_id,
            "verdict": verdict,
            "confidence": confidence,
            "uploaded_at": now_iso
        }
    finally:
        conn.close()


def get_case_evidence(case_id: str) -> List[dict]:
    """Retrieve all evidence items attached to a specific case."""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM evidence WHERE case_id = ? ORDER BY uploaded_at DESC
        """, (case_id,))
        rows = cursor.fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


# Initialize database on module load
init_db()
