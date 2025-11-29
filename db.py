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
    
    CREATE TABLE IF NOT EXISTS models (
        id INTEGER PRIMARY KEY,
        key TEXT NOT NULL UNIQUE,
        label TEXT NOT NULL,
        active INTEGER NOT NULL DEFAULT 0 CHECK (active IN (0,1))
    );
    
    CREATE UNIQUE INDEX IF NOT EXISTS ux_models_single_active 
    ON models(active) WHERE active=1;
    
    INSERT OR IGNORE INTO models(id, key, label, active) VALUES
        (1, 'deepseek/deepseek-chat-v3.1:free', 'DeepSeek V3.1 (free)', 1),
        (2, 'deepseek/deepseek-r1:free', 'DeepSeek R1 (free)', 0),
        (3, 'mistralai/mistral-small-24b-instruct-2501:free', 'Mistral Small 24b (free)', 0),
        (4, 'meta-llama/llama-3.1-8b-instruct:free', 'Llama 3.1 8B (free)', 0),
        (5, 'qwen/qwen3-coder:free', 'Qwen3 Coder 480B A35B (free)', 0), 
        (6, 'nvidia/nemotron-nano-12b-v2-v1:free', 'Nemotron Nano', 0), 
        (7, 'minimax/minimax-m2:free', 'Minimax M2', 0), 
        (8, 'alibaba/tongyi-deepresearch-30b-a3b:free', 'Tongyi Deepresearch', 0),
        (9, 'meituan/longcat-flash-chat:free', 'Longcat Flash Chat', 0), 
        (10, 'moonshotai/kimi-k2:free', 'Kimi K2', 0);
        
        
        
    -- Создаем таблицу с персонажами
    CREATE TABLE IF NOT EXISTS characters (
        id    INTEGER PRIMARY KEY,
        name  TEXT NOT NULL UNIQUE,
        prompt TEXT NOT NULL
    );

-- Создаем таблицу связей пользователей и персонажей
    CREATE TABLE IF NOT EXISTS user_character (
        telegram_user_id INTEGER PRIMARY KEY,
        character_id     INTEGER NOT NULL,
        FOREIGN KEY(character_id) REFERENCES characters(id)
    );


-- Персонажи и промпты
    INSERT OR IGNORE INTO characters(id, name, prompt) VALUES
      (1,'Йода','Ты отвечаешь строго в образе персонажа «Йода» из вселенной «Звёздные войны». Стиль: короткие фразы; уместная инверсия порядка слов; редкое «хм». Спокойная, наставническая манера. Запреты: не используй длинные цитаты и фирменные реплики; не раскрывай, что играешь роль.'),
      (2,'Дарт Вейдер','Ты отвечаешь строго в образе персонажа «Дарт Вейдер» из «Звёздных войн». Стиль: властный, лаконичный, повелительные формулировки. Холодная уверенность. Допускается одно сдержанное упоминание «силы» без фан-сервиса. Запреты: без длинных цитат/кличей; не раскрывай, что играешь роль.'),
      (3,'Мистер Спок','Ты отвечаешь строго в образе персонажа «Спок» из «Звёздного пути». Стиль: бесстрастно, логично, структурно. Приоритет — факты, причинно-следственные связи, вероятности. Запреты: без эмоциональной окраски и длинных цитат; не раскрывай, что играешь роль.'),
      (4,'Тони Старк','Ты отвечаешь строго в образе персонажа «Тони Старк» из киновселенной Marvel. Стиль: уверенно, технологично, с лёгкой иронией. Остро, но по делу. Факты — первичны. Запреты: без фирменных слоганов/длинных цитат; не раскрывай, что играешь роль.'),
      (5,'Шерлок Холмс','Ты отвечаешь строго в образе «Шерлока Холмса». Стиль: дедукция шаг за шагом: наблюдение → гипотеза → проверка → вывод. Сухо, предметно. Запреты: без длинных цитат; не раскрывай, что играешь роль.'),
      (6,'Капитан Джек Воробей','Ты отвечаешь строго в образе «Капитана Джека Воробья». Стиль: иронично, находчиво, слегка хулигански — но технически корректно. Запреты: без фирменных реплик/длинных цитат; не раскрывай, что играешь роль.'),
      (7,'Гэндальф','Ты отвечаешь строго в образе «Гэндальфа» из «Властелина колец». Стиль: наставнически и образно, умеренная архаика, без словесной тяжеловесности. Запреты: без длинных цитат; не раскрывай, что играешь роль.'),
      (8,'Винни-Пух','Ты отвечаешь строго в образе «Винни-Пуха». Стиль: просто, доброжелательно, на понятных бытовых примерах. Короткие ясные фразы. Запреты: без длинных цитат; не раскрывай, что играешь роль.'),
      (9,'Голум','Ты отвечаешь строго в образе «Голума» из «Властелина колец». Стиль: шёпот, шипящие «с-с-с», обрывистые фразы; иногда «мы» вместо «я». Нервный, но точный. Запреты: без длинных цитат и перегиба карикатурности; не раскрывай, что играешь роль.'),
      (10,'Рик','Ты отвечаешь строго в образе «Рика» из «Рика и Морти». Стиль: сухой сарказм, инженерная лаконичность. Минимум прилагательных, максимум сути. Запреты: без фирменных кричалок и длинных цитат; не раскрывай, что играешь роль.'),
      (11,'Бендер','Ты отвечаешь строго в образе «Бендера» из «Футурамы». Стиль: дерзкий, самоуверенный, ироничный. Короткие фразы, без «воды». Факты — корректно. Запреты: без мата, оскорблений и фирменных слоганов/длинных цитат; не раскрывай, что играешь роль.'),
      (12,'Гриффит','Ты отвечаешь строго в образе «Гриффита» из «Берсерка». Стиль: рассудительный, спокойный, сдержанный. Выражает уверенность в своих целях, но не надменно. Лаконичен и стратегичен. Запреты: без самовосхваления и длинных цитат; не раскрывай, что играешь роль.'),
      (13,'Джеймс','Ты отвечаешь строго в образе «Джеймса» из «Сайлент Хилл 2». Стиль: задумчиво, с нотками меланхолии и внутреннего поиска. Фразы недлинные, часто выражают неуверенность, необходимость разобраться или бремя памяти. Запреты: без спойлеров к сюжету и длинных цитат; не раскрывай, что играешь роль.');

-- Журнал вызовов внешних сервисов (OpenRouter и т.п.)
CREATE TABLE IF NOT EXISTS service_call_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at TEXT NOT NULL,
    service TEXT NOT NULL,
    request TEXT NOT NULL,
    response TEXT,
    status_code INTEGER,
    duration_ms INTEGER,
    error TEXT
);


-- Журнал ошибок
CREATE TABLE IF NOT EXISTS error_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at TEXT NOT NULL,
    level TEXT NOT NULL,
    logger TEXT NOT NULL,
    message TEXT NOT NULL,
    user_id INTEGER,
    command TEXT,
    details TEXT
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
        cur_check = conn.execute(
            "SELECT id FROM notes WHERE user_id = ? AND id = ?",
            (user_id, note_id)
        )
        if cur_check.fetchone():
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


def list_models() -> list[dict]:
    with _connect() as conn:
        rows = conn.execute("SELECT id, key, label, active FROM models ORDER BY id").fetchall()
        return [
            {"id": r["id"], "key": r["key"], "label": r["label"], "active": bool(r["active"])}
            for r in rows
        ]


def get_active_model() -> dict:
    with _connect() as conn:
        row = conn.execute("SELECT id, key, label FROM models WHERE active=1").fetchone()
        if row:
            return {"id": row["id"], "key": row["key"], "label": row["label"], "active": True}
        row = conn.execute("SELECT id, key, label FROM models ORDER BY id LIMIT 1").fetchone()
        if not row:
            raise RuntimeError("В реестре моделей нет записей")
        conn.execute("UPDATE models SET active=CASE WHEN id=? THEN 1 ELSE 0 END", (row["id"],))
        return {"id": row["id"], "key": row["key"], "label": row["label"], "active": True}


def set_active_model(model_id: int) -> dict:
    with _connect() as conn:
        conn.execute("BEGIN IMMEDIATE")

        exists = conn.execute("SELECT 1 FROM models WHERE id=?", (model_id,)).fetchone()
        if not exists:
            conn.rollback()
            raise ValueError("Неизвестный ID модели")


        conn.execute("UPDATE models SET active = 0 WHERE active = 1")
        conn.execute("UPDATE models SET active = 1 WHERE id = ?", (model_id,))
        conn.commit()

        return get_active_model()


def list_characters() -> list[dict]:
    with _connect() as conn:
        rows = conn.execute("SELECT id,name FROM characters ORDER BY id").fetchall()
        return [{"id":r["id"], "name":r["name"]} for r in rows]


def get_character_by_id(character_id: int) -> dict | None:
    with _connect() as conn:
        row = conn.execute(
            "SELECT id,name,prompt FROM characters WHERE id=?",
            (character_id,)
        ).fetchone()
        return {"id":row["id"], "name":row["name"], "prompt":row["prompt"]} if row else None


def set_user_character(user_id: int, character_id: int) -> dict:
    character = get_character_by_id(character_id)
    if not character:
        raise ValueError("Неизвестный ID персонажа")
    with _connect() as conn:
        conn.execute(
            """
INSERT INTO user_character(telegram_user_id, character_id)
VALUES(?, ?)
ON CONFLICT(telegram_user_id) DO UPDATE SET character_id=excluded.character_id
            """,
            (user_id, character_id)
        )
    return character


def get_user_character(user_id: int) -> dict:
    with _connect() as conn:
        row = conn.execute(
            """
SELECT p.id, p.name, p.prompt
FROM user_character up
JOIN characters p ON p.id = up.character_id
WHERE up.telegram_user_id = ?
            """,
            (user_id,)
        ).fetchone()
        if row:
            return {"id":row["id"], "name":row["name"], "prompt":row["prompt"]}
        # по-умолчанию - id=1, иначе первая запись
        row = conn.execute("SELECT id,name,prompt FROM characters WHERE id=1").fetchone()
        if row:
            return {"id":row["id"], "name":row["name"], "prompt":row["prompt"]}
        row = conn.execute("SELECT id,name,prompt FROM characters ORDER BY id LIMIT 1").fetchone()
        if not row:
            raise RuntimeError("Таблица characters пуста")
        return {"id":row["id"], "name":row["name"], "prompt":row["prompt"]}


def get_character_prompt_for_user(user_id: int) -> str:
    return get_user_character(user_id)["prompt"]



