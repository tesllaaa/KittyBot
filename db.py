import os
import sqlite3

DB_PATH = os.getenv("DB_PATH", "bot.db")

def _connect():
    conn = sqlite3.connect(DB_PATH, timeout=5.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    conn.execute("PRAGMA busy_timeout = 5000")
    return conn

def init_db():
    schema = """
    CREATE TABLE IF NOT EXISTS notes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    text TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    
        CREATE TABLE IF NOT EXISTS activity_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        action TEXT NOT NULL, -- 'create' или 'delete'
        note_id INTEGER,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """
    with _connect() as conn:
        conn.executescript(schema)


def add_note(user_id: int, text: str) -> int:
    with _connect() as conn:
        cur_count = conn.execute(
            "SELECT COUNT(id) FROM notes WHERE user_id = ?",
            (user_id,)
        )
        count = cur_count.fetchone()[0]

        if count >= 50:
            return 0

        cur = conn.execute(
            "INSERT INTO notes(user_id, text) VALUES (?, ?)",
            (user_id, text)
        )
        note_id = cur.lastrowid

        conn.execute(
            "INSERT INTO activity_log(user_id, action, note_id) VALUES (?, 'create', ?)",
            (user_id, note_id)
        )

    return note_id


def list_notes(user_id: int, limit: int = 10):
    with _connect() as conn:
        cur = conn.execute(
            """SELECT id, text, created_at
            FROM notes
            WHERE user_id = ?
            ORDER BY id DESC
            LIMIT ?""",
            (user_id, limit)
        )
    return cur.fetchall()


def update_note(user_id: int, note_id: int, text: str) -> bool:
    with _connect() as conn:
        cur = conn.execute(
            """UPDATE notes
            SET text = ?
            WHERE user_id = ? AND id = ?""",
            (text, user_id, note_id)
        )
    return cur.rowcount > 0


def delete_note(user_id: int, note_id: int) -> bool:
    with _connect() as conn:
        cur_check = conn.execute("SELECT id FROM notes WHERE user_id = ? AND id = ?", (user_id, note_id))
        if cur_check.fetchone():
            # Добавляем запись в журнал
            conn.execute(
                "INSERT INTO activity_log(user_id, action, note_id) VALUES (?, 'delete', ?)",
                (user_id, note_id)
            )
            cur_del = conn.execute(
                "DELETE FROM notes WHERE user_id = ? AND id = ?",
                (user_id, note_id)
            )
            return cur_del.rowcount > 0
    return False


def find_notes(user_id: int, query_text: str, limit: int = 10):
    with _connect() as conn:
        cur = conn.execute(
            """SELECT id, text
            FROM notes
            WHERE user_id = ?
            AND text LIKE '%' || ? || '%'
            ORDER BY id DESC
            LIMIT ?""",
            (user_id, query_text, limit)
        )
    return cur.fetchall()


def list_all_notes(user_id: int):

    with _connect() as conn:
        cur = conn.execute(
            """SELECT id, text, created_at
            FROM notes
            WHERE user_id = ?
            ORDER BY id ASC""",
            (user_id,)
        )
    return cur.fetchall()


def get_weekly_stats(user_id: int):

    stats = {'create': 0, 'delete': 0}
    with _connect() as conn:
        # Добавляем условие для выборки записей за последние 7 дней
        cur = conn.execute(
            """SELECT action, COUNT(id) as count
            FROM activity_log
            WHERE user_id = ? AND created_at >= datetime('now', '-7 days')
            GROUP BY action""",
            (user_id,)
        )
        rows = cur.fetchall()

    for row in rows:
        if row['action'] in stats:
            stats[row['action']] = row['count']

    return stats