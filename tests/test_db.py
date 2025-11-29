def test_character_upsert(db_module):
    db = db_module
    # Предполагаем, что список персонажей уже есть. Берём любую существующую запись.
    characters = db.list_characters() if hasattr(db, "list_characters") else db.list_characters()
    assert characters, "Список персонажей пуст - проверь schema в db.py"
    any_id = characters[0]["id"]

    uid = 777001
    db.set_user_character(uid, any_id)
    p1 = db.get_user_character(uid)
    assert p1["id"] == any_id

    # Выберем другого персонажа и убедимся, что запись обновилась
    other_id = characters[-1]["id"] if characters[-1]["id"] != any_id else characters[1]["id"]
    db.set_user_character(uid, other_id)
    p2 = db.get_user_character(uid)
    assert p2["id"] == other_id

def test_models_single_active_switch(db_module):
    db = db_module
    models = db.list_models()
    assert len(models) >= 2, "Нужно >= 2 моделей в списке"
    a, b = models[0]["id"], models[1]["id"]

    # Сделать активной A
    db.set_active_model(a)
    act = db.get_active_model()
    assert act["id"] == a

    # Сделать активной B
    db.set_active_model(b)
    act2 = db.get_active_model()
    assert act2["id"] == b

    # Ровно одна активная
    with db._connect() as conn:
        cnt = conn.execute("SELECT COUNT(*) FROM models WHERE active=1").fetchone()[0]
        assert cnt == 1, "Должна быть ровно одна активная модель"


import pytest

def test_set_active_model_rejects_unknown_id(db_module):
    db = db_module

    # Берём гарантированно несуществующий ID (например, очень большое число)
    unknown_id = 999999

    with pytest.raises(ValueError) as excinfo:
        db.set_active_model(unknown_id)

    # Сообщение об ошибке из db.py:
    assert "Неизвестный ID модели" in str(excinfo.value)


def test_set_user_character_rejects_unknown_id(db_module):
    db = db_module
    user_id = 777002
    unknown_character_id = 999999

    with pytest.raises(ValueError) as excinfo:
        db.set_user_character(user_id, unknown_character_id)

    assert "Неизвестный ID персонажа" in str(excinfo.value)


def test_get_user_character_falls_back_to_default(db_module):
    db = db_module

    # Берём пользователя, для которого мы точно ничего не записывали
    uid = 999001

    # Вызов без предварительного set_user_character
    ch = db.get_user_character(uid)

    # Ожидание: нам вернётся существующий персонаж из таблицы characters
    all_chars = db.list_characters()
    assert all_chars, "Список персонажей пуст - проверь schema в db.py"

    ids = {c["id"] for c in all_chars}
    assert ch["id"] in ids, "get_user_character должен возвращать одного из существующих персонажей"


def test_list_all_notes_empty_for_new_user(db_module):
    """Для нового пользователя список заметок пуст"""
    db = db_module
    uid = 888001  # Гарантированно новый пользователь

    notes = db.list_all_notes(uid)

    assert notes == [], "Для нового пользователя список заметок должен быть пуст"


def test_list_all_notes_returns_correct_structure(db_module):
    """Возвращает заметки с правильной структурой (id, text, created_at)"""
    db = db_module
    uid = 888002

    # Предполагаем наличие функции add_note
    db.add_note(uid, "Тестовая заметка")
    notes = db.list_all_notes(uid)

    assert len(notes) >= 1, "Должна быть хотя бы одна заметка"
    note = notes[0]
    assert "id" in note
    assert "text" in note
    assert "created_at" in note


def test_list_all_notes_ordered_by_id_ascending(db_module):
    """Заметки отсортированы по id по возрастанию"""
    db = db_module
    uid = 888003

    db.add_note(uid, "Первая")
    db.add_note(uid, "Вторая")
    db.add_note(uid, "Третья")

    notes = db.list_all_notes(uid)
    ids = [n["id"] for n in notes]

    assert ids == sorted(ids), "Заметки должны быть отсортированы по id ASC"


def test_list_all_notes_user_isolation(db_module):
    """Заметки одного пользователя не видны другому"""
    db = db_module
    uid1, uid2 = 888004, 888005

    db.add_note(uid1, "Приватная заметка user1")
    db.add_note(uid2, "Приватная заметка user2")

    notes1 = db.list_all_notes(uid1)
    notes2 = db.list_all_notes(uid2)

    # ID заметок не должны пересекаться
    ids1 = {n["id"] for n in notes1}
    ids2 = {n["id"] for n in notes2}
    assert ids1.isdisjoint(ids2), "Заметки разных пользователей не должны смешиваться"


def test_list_all_notes_contains_added_text(db_module):
    """Добавленная заметка появляется в списке с правильным текстом"""
    db = db_module
    uid = 888006
    expected_text = "Уникальный текст заметки 12345"

    db.add_note(uid, expected_text)
    notes = db.list_all_notes(uid)

    texts = [n["text"] for n in notes]
    assert expected_text in texts, "Добавленная заметка должна быть в списке"