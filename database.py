import sqlite3
from pathlib import Path
from datetime import datetime

DB_PATH = Path(__file__).parent / "questions.db"


def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    c.execute('''CREATE TABLE IF NOT EXISTS raw_cases (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        pmc_id      TEXT UNIQUE,
        title       TEXT,
        full_text   TEXT,
        image_urls  TEXT,
        url         TEXT,
        fetched_at  TEXT,
        processed   INTEGER DEFAULT 0
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS questions (
        id              INTEGER PRIMARY KEY AUTOINCREMENT,
        pmc_id          TEXT,
        case_title      TEXT,
        question_text   TEXT,
        option_a        TEXT,
        option_b        TEXT,
        option_c        TEXT,
        option_d        TEXT,
        correct_answer  TEXT,
        explanation     TEXT,
        category        TEXT,
        difficulty      TEXT,
        image_url       TEXT,
        image_caption   TEXT,
        status          TEXT DEFAULT 'pending',
        created_at      TEXT,
        reviewed_at     TEXT
    )''')

    conn.commit()
    conn.close()
    print(f"Database ready at: {DB_PATH}")


def get_unprocessed_cases(limit=10):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT * FROM raw_cases WHERE processed=0 LIMIT ?", (limit,))
    rows = [dict(r) for r in c.fetchall()]
    conn.close()
    return rows


def mark_case_processed(pmc_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("UPDATE raw_cases SET processed=1 WHERE pmc_id=?", (pmc_id,))
    conn.commit()
    conn.close()


def save_question(q: dict):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''INSERT INTO questions
        (pmc_id, case_title, question_text, option_a, option_b, option_c, option_d,
         correct_answer, explanation, category, difficulty, image_url, image_caption, created_at)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)''', (
        q.get("pmc_id"), q.get("case_title"), q.get("question_text"),
        q.get("option_a"), q.get("option_b"), q.get("option_c"), q.get("option_d"),
        q.get("correct_answer"), q.get("explanation"),
        q.get("category"), q.get("difficulty"),
        q.get("image_url"), q.get("image_caption"),
        datetime.now().isoformat()
    ))
    conn.commit()
    conn.close()


def get_pending_questions(limit=50):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT * FROM questions WHERE status='pending' ORDER BY id DESC LIMIT ?", (limit,))
    rows = [dict(r) for r in c.fetchall()]
    conn.close()
    return rows


def update_question_status(question_id: int, status: str, updated_text: dict = None):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    if updated_text:
        c.execute('''UPDATE questions SET status=?, reviewed_at=?,
                     question_text=?, option_a=?, option_b=?, option_c=?, option_d=?,
                     correct_answer=?, explanation=?
                     WHERE id=?''', (
            status, datetime.now().isoformat(),
            updated_text.get("question_text"),
            updated_text.get("option_a"), updated_text.get("option_b"),
            updated_text.get("option_c"), updated_text.get("option_d"),
            updated_text.get("correct_answer"), updated_text.get("explanation"),
            question_id
        ))
    else:
        c.execute("UPDATE questions SET status=?, reviewed_at=? WHERE id=?",
                  (status, datetime.now().isoformat(), question_id))
    conn.commit()
    conn.close()


def get_stats():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    stats = {}
    c.execute("SELECT COUNT(*) FROM raw_cases")
    stats["total_cases"] = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM raw_cases WHERE processed=1")
    stats["processed_cases"] = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM questions")
    stats["total_questions"] = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM questions WHERE status='pending'")
    stats["pending"] = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM questions WHERE status='approved'")
    stats["approved"] = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM questions WHERE status='rejected'")
    stats["rejected"] = c.fetchone()[0]
    conn.close()
    return stats
