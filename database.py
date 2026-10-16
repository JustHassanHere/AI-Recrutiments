import sqlite3
import json

DB_NAME = "recruitment.db"


def get_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn


def create_tables():
    conn = get_connection()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            description TEXT,
            requirements TEXT,
            must_have TEXT
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS candidates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            job_id INTEGER,
            message_id TEXT,
            filename TEXT,
            file_path TEXT,
            sender TEXT,
            subject TEXT,
            cv_info TEXT,
            results TEXT,
            decision TEXT DEFAULT 'Pending',
            UNIQUE(job_id, message_id, filename)
        )
    """)
    conn.commit()
    conn.close()


def row_to_job(row):
    job = dict(row)
    job["requirements"] = json.loads(job["requirements"])
    job["must_have"] = json.loads(job["must_have"])
    return job


def create_job(title, description, requirements):
    conn = get_connection()
    cursor = conn.execute(
        "INSERT INTO jobs (title, description, requirements, must_have) VALUES (?, ?, ?, ?)",
        (title, description, json.dumps(requirements), json.dumps([])),
    )
    conn.commit()
    job_id = cursor.lastrowid
    conn.close()
    return job_id


def get_job(job_id):
    conn = get_connection()
    row = conn.execute("SELECT * FROM jobs WHERE id = ?", (job_id,)).fetchone()
    conn.close()
    if row is None:
        return None
    return row_to_job(row)


def get_all_jobs():
    conn = get_connection()
    rows = conn.execute("SELECT * FROM jobs ORDER BY id").fetchall()
    conn.close()
    return [row_to_job(row) for row in rows]


def update_must_have(job_id, must_have):
    conn = get_connection()
    conn.execute("UPDATE jobs SET must_have = ? WHERE id = ?", (json.dumps(must_have), job_id))
    conn.commit()
    conn.close()


def row_to_candidate(row):
    candidate = dict(row)
    candidate["cv_info"] = json.loads(candidate["cv_info"])
    candidate["results"] = json.loads(candidate["results"])
    return candidate


def candidate_exists(job_id, message_id, filename):
    conn = get_connection()
    row = conn.execute(
        "SELECT id FROM candidates WHERE job_id = ? AND message_id = ? AND filename = ?",
        (job_id, message_id, filename),
    ).fetchone()
    conn.close()
    return row is not None


def save_candidate(job_id, message_id, filename, file_path, sender, subject, cv_info, results):
    conn = get_connection()
    conn.execute(
        """INSERT OR IGNORE INTO candidates
           (job_id, message_id, filename, file_path, sender, subject, cv_info, results)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (job_id, message_id, filename, str(file_path), sender, subject,
         json.dumps(cv_info), json.dumps(results)),
    )
    conn.commit()
    conn.close()


def get_candidates(job_id):
    conn = get_connection()
    rows = conn.execute("SELECT * FROM candidates WHERE job_id = ?", (job_id,)).fetchall()
    conn.close()
    return [row_to_candidate(row) for row in rows]


def get_candidate(candidate_id):
    conn = get_connection()
    row = conn.execute("SELECT * FROM candidates WHERE id = ?", (candidate_id,)).fetchone()
    conn.close()
    if row is None:
        return None
    return row_to_candidate(row)


def update_decision(candidate_id, decision):
    conn = get_connection()
    conn.execute("UPDATE candidates SET decision = ? WHERE id = ?", (decision, candidate_id))
    conn.commit()
    conn.close()