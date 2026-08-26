import sqlite3
from datetime import datetime
from pathlib import Path

DB_PATH = Path(__file__).parent / "audit.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS audit_log (
            id               INTEGER PRIMARY KEY AUTOINCREMENT,
            event_id         TEXT,
            customer_name    TEXT,
            customer_email   TEXT,
            amount_inr       REAL,
            failure_reason   TEXT,
            agent            TEXT,
            action           TEXT,
            outcome          TEXT,
            amount_recovered REAL DEFAULT 0,
            reason           TEXT,
            timestamp        TEXT
        )
    """)
    conn.commit()
    conn.close()

def log_action(
    event_id: str,
    customer_name: str,
    customer_email: str,
    amount_inr: float,
    failure_reason: str,
    agent: str,
    action: str,
    outcome: str,
    amount_recovered: float = 0,
    reason: str = ""
):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO audit_log (
            event_id, customer_name, customer_email, amount_inr,
            failure_reason, agent, action, outcome,
            amount_recovered, reason, timestamp
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        event_id, customer_name, customer_email, amount_inr,
        failure_reason, agent, action, outcome,
        amount_recovered, reason,
        datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ))
    conn.commit()
    conn.close()

def get_all_logs():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM audit_log ORDER BY id ASC")
    rows = cursor.fetchall()
    columns = [desc[0] for desc in cursor.description]
    conn.close()
    return columns, rows

def clear_logs():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM audit_log")
    conn.commit()
    conn.close()
