import os
import random

from dotenv import load_dotenv
import telebot
from telebot import types
import time
from db import init_db, add_note, list_notes, update_note, delete_note, find_notes, list_all_notes, get_weekly_stats, \
    get_active_model, set_active_model, list_models, get_character_by_id, list_characters, get_user_character, \
    set_user_character
from openrouter_client import OpenRouterError, chat_once

# Загрузка переменных окружения
load_dotenv()
TOKEN = os.getenv("TOKEN")
if not TOKEN:
    raise RuntimeError("В .env файле нет TOKEN")

bot = telebot.TeleBot(TOKEN)

# Инициализация базы данных при запуске
init_db()


def _build_messages(user_id: int, user_text: str) -> list[dict]:
    p = get_user_character(user_id)
    system = (
        f"Ты отвечаешь строго в образе персонажа: {p['name']}.\n"
        f"{p['prompt']}\n\n"
        "Правила:\n"
        "1) Всегда держи стиль и манеру речи выбранного персонажа. При необходимости - переформулируй.\n"
        "2) Технические ответы давай корректно и по пунктам, но в характерной манере.\n"
        "3) Не раскрывай, что ты 'играешь роль'.\n"
        "4) Не используй длинные дословные цитаты из фильмов/книг (>10 слов).\n"
        "5) Если стиль персонажа выражен слабо - переформулируй ответ и усили характер персонажа, сохраняя фактическую точность.\n"
    )
    return [
        {"role": "system", "content": system},
        {"role": "user", "content": user_text},
    ]

def _build_messages_for_character(character: dict, user_text: str) -> list[dict]:
    system = (
        f"Ты отвечаешь строго в образе персонажа: {character['name']}.\n"
        f"{character['prompt']}\n"
        "Правила:\n"
        "1) Всегда держи стиль и манеру речи выбранного персонажа. При необходимости – переформулируй.\n"
        "2) Технические ответы давай корректно и по пунктам, но в характерной манере.\n"
        "3) Не раскрывай, что ты 'играешь роль'.\n"
        "4) Не используй длинные дословные цитаты из фильмов/книг (>10 слов).\n"
        "5) Если стиль персонажа выражен слабо – переформулируй ответ и усили характер персонажа, сохраняя фактическую точность.\n"
    )

    return [
        {"role": "system", "content": system},
        {"role": "user", "content": user_text},
    ]


@bot.message_handler(commands=["characters"])
def cmd_characters(message: types.Message) -> None:
    """Показать список персонажей"""
    user_id = message.from_user.id
    items = list_characters()
    if not items:
        bot.reply_to(message, text="Каталог персонажей пуст.")
        return

    # Текущий персонаж пользователя
    try:
        current = get_user_character(user_id)["id"]
    except Exception:
        current = None

    lines = ["Доступные персонажи:"]
    for p in items:
        star = "★" if current is not None and p["id"] == current else ""
        lines.append(f"{star}{p['id']}. {p['name']}")
    lines.append("\nВыбор: /character <ID>")
    bot.reply_to(message, "\n".join(lines))


@bot.message_handler(commands=["character"])
def cmd_character(message: types.Message) -> None:
    """Установить активным персонажа"""
    user_id = message.from_user.id
    arg = message.text.replace("/character", "", 1).strip()
    if not arg:
        p = get_user_character(user_id)
        bot.reply_to(message, f"Текущий персонаж: {p['name']}\n(сменить: /characters, затем /character <ID>)")
        return
    if not arg.isdigit():
        bot.reply_to(message, text="Использование: /character <ID из /characters>")
        return

    try:
        p = set_user_character(user_id, int(arg))
        bot.reply_to(message, text=f"Персонаж установлен: {p['name']}")
    except ValueError:
        bot.reply_to(message, text="Неизвестный ID персонажа. Сначала /characters.")


@bot.message_handler(commands=["whoami"])
def cmd_whoami(message: types.Message) -> None:
    """Показать активную модель и активного персонажа"""
    character = get_user_character(message.from_user.id)
    model = get_active_model()
    bot.reply_to(message, text=f"Модель: {model['label']} [{model['key']}]\nПерсонаж: {character['name']}")



@bot.message_handler(commands=["ask_random"])
def cmd_ask_random(message: types.Message) -> None:
    q = message.text.replace("/ask_random","", 1).strip()
    if not q:
        bot.reply_to(message, text="Использование: /ask_random <вопрос>")
        return
    q = q[:600]

    # Берём случайного персонажа из таблицы (НЕ сохраняем в user_character)
    items = list_characters()
    if not items:
        bot.reply_to(message, text="Каталог персонажей пуст.")
        return
    chosen = random.choice(items)
    character = get_character_by_id(chosen["id"]) # получаем prompt


    msgs = _build_messages_for_character(character, q)
    model_key = get_active_model()["key"]

    try:
        text, ms = chat_once(msgs, model=model_key, temperature=0.2, max_tokens=400)
        out = (text or "").strip()[:4000]
        bot.reply_to(message, text=f"{out}\n\n{ms} мс; модель: {model_key}; как: {character['name']}")
    except OpenRouterError as e:
        bot.reply_to(message, text=f"Ошибка: {e}")
    except Exception:
        bot.reply_to(message, text="Непредвиденная ошибка.")



@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, "Привет! Я бот для заметок. Используй /help для списка команд.")

@bot.message_handler(commands=['help'])
def help_cmd(message):
    help_text = """
Доступные команды:
/note_add <текст> - Добавить заметку
/note_list - Показать все заметки
/note_find <запрос> - Найти заметку
/note_edit <id> <новый текст> - Изменить заметку
/note_del <id> - Удалить заметку
/note_export - Экспортировать заметки
/stats - Еженедельная статистика
/ask - Вопрос
"""
    bot.reply_to(message, help_text)

@bot.message_handler(commands=['note_add'])
def note_add(message):
    text = message.text.replace('/note_add', '').strip()
    if not text:
        bot.reply_to(message, "Ошибка: Укажите текст заметки.")
        return

    user_id = message.from_user.id
    note_id = add_note(user_id, text)


    if note_id > 0:
        bot.reply_to(message, f"Заметка #{note_id} добавлена: {text}")
    else:
        error_message = (
            f"❌ Достигнут лимит заметок ({50} шт.)\n\n"
            "Чтобы добавить новую, удалите одну из старых заметок с помощью команды /note_del <id>."
        )
        bot.reply_to(message, error_message)

@bot.message_handler(commands=['note_list'])
def note_list(message):
    user_id = message.from_user.id
    user_notes = list_notes(user_id)

    if not user_notes:
        bot.reply_to(message, "Заметок пока нет.")
        return

    response = "Ваши заметки:\n" + "\n".join([f"{note['id']}: {note['text']}" for note in user_notes])
    bot.reply_to(message, response)

@bot.message_handler(commands=["models"])
def cmd_models(message: types.Message) -> None:
    items = list_models()
    if not items:
        bot.reply_to(message, "Список моделей пуст.")
        return
    lines = ["Доступные модели:"]
    for m in items:
        star = "★" if m["active"] else " "
        lines.append(f"{star} {m['id']}. {m['label']}  [{m['key']}]")
    lines.append("\nАктивировать: /model <ID>")
    bot.reply_to(message, "\n".join(lines))


@bot.message_handler(commands=["model"])
def cmd_model(message: types.Message) -> None:
    arg = message.text.replace("/model", "", 1).strip()
    if not arg:
        active = get_active_model()
        bot.reply_to(message, text=f"Текущая активная модель: {active['label']} [{active['key']}]\n(сменить: /model <ID> или /models)")
        return
    if not arg.isdigit():
        bot.reply_to(message, text="Использование: /model <ID из /models>")
        return
    try:
        active = set_active_model(int(arg))
        bot.reply_to(message, text=f"Активная модель переключена: {active['label']} [{active['key']}]")
    except ValueError:
        bot.reply_to(message, text="Неизвестный ID модели. Сначала /models.")


@bot.message_handler(commands=["ask"])
def cmd_ask(message: types.Message) -> None:
    q = message. text.replace ("/ask", "", 1) .strip()
    if not q:
        bot.reply_to(message, "Использование: /ask <вопрос>")
        return

    msgs = _build_messages(message.from_user.id, q[:600])
    model_key = get_active_model() ["key"]

    try:
        text, ms = chat_once(msgs, model=model_key, temperature=0.2, max_tokens=400)
        out = (text or "") .strip()[: 4000]
        bot.reply_to(message, f"{out}\n\n({ms} мc; модель: {model_key})")
    except OpenRouterError as e:
        bot.reply_to(message, f"Ошибка: {e}")
    except Exception:
        bot.reply_to(message, "Непредвиденная ошибка. ")


@bot.message_handler(commands=["ask_model"])
def cmd_ask_model(message: types.Message):
    parts = message.text.split(maxsplit=2)

    # /ask_model <id> <question>
    if len(parts) < 3:
        bot.reply_to(message, "Использование: /ask_model <ID> <вопрос>")
        return

    model_id_str, question = parts[1], parts[2]

    if not model_id_str.isdigit():
        bot.reply_to(message, "ID модели должен быть числом.")
        return

    model_id = int(model_id_str)

    # Получаем модель по ID
    models = list_models()
    target_model = next((m for m in models if m["id"] == model_id), None)

    if not target_model:
        bot.reply_to(message, f"Модель с ID={model_id} не найдена.")
        return

    model_key = target_model["key"]
    msgs = _build_messages(message.from_user.id, question[:600])

    try:
        text, ms = chat_once(msgs, model=model_key, temperature=0.2, max_tokens=400)
        result = (text or "").strip()[:4000]
        bot.reply_to(message, f"{result}\n\n({ms} мс; модель: {model_key})")
    except OpenRouterError as e:
        bot.reply_to(message, f"Ошибка: {e}")
    except Exception:
        bot.reply_to(message, "Произошла непредвиденная ошибка.")


@bot.message_handler(commands=['note_find'])
def note_find(message):
    query_text = message.text.replace('/note_find', '').strip()
    if not query_text:
        bot.reply_to(message, "Ошибка: Укажите текст для поиска после команды.")
        return

    user_id = message.from_user.id
    found_notes = find_notes(user_id, query_text)

    if not found_notes:
        bot.reply_to(message, f"Ничего не найдено по запросу: «{query_text}»")
        return

    response = "Результаты поиска:\n" + "\n".join([f"{note['id']}: {note['text']}" for note in found_notes])
    bot.reply_to(message, response)

@bot.message_handler(commands=['note_edit'])
def note_edit(message):
    parts = message.text.split(maxsplit=2)
    if len(parts) < 3:
        bot.reply_to(message, "Ошибка: Используйте /note_edit <id> <новый текст>")
        return

    try:
        note_id = int(parts[1])
        new_text = parts[2]
    except ValueError:
        bot.reply_to(message, "Ошибка: ID должен быть числом.")
        return

    user_id = message.from_user.id
    success = update_note(user_id, note_id, new_text)

    if not success:
        bot.reply_to(message, f"Ошибка: Заметка #{note_id} не найдена или у вас нет прав для её изменения.")
        return

    bot.reply_to(message, f"Заметка #{note_id} изменена на: {new_text}")

@bot.message_handler(commands=['note_del'])
def note_del(message):
    parts = message.text.split()
    if len(parts) < 2:
        bot.reply_to(message, "Ошибка: Укажите ID заметки для удаления.")
        return

    try:
        note_id = int(parts[1])
    except ValueError:
        bot.reply_to(message, "Ошибка: ID должен быть числом.")
        return

    user_id = message.from_user.id
    success = delete_note(user_id, note_id)

    if not success:
        bot.reply_to(message, f"Ошибка: Заметка #{note_id} не найдена или у вас нет прав для её удаления.")
        return

    bot.reply_to(message, f"Заметка #{note_id} удалена.")


@bot.message_handler(commands=['note_export'])
def note_export(message):
    user_id = message.from_user.id
    all_notes = list_all_notes(user_id)

    if not all_notes:
        bot.reply_to(message, "У вас нет заметок для экспорта.")
        return

    file_path = f"notes_{user_id}.txt"

    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            username = message.from_user.username or f"user_{user_id}"
            f.write(f"Экспорт всех заметок для пользователя @{username}\n")
            f.write("="*30 + "\n\n")
            for note in all_notes:
                f.write(f"ID: {note['id']}\n")
                f.write(f"Дата создания: {note['created_at']}\n")
                f.write(f"Текст: {note['text']}\n")
                f.write("-"*20 + "\n\n")

        with open(file_path, 'rb') as f:
            bot.send_document(message.chat.id, f, caption="Ваши заметки в файле.")

    except Exception as e:
        print(f"Ошибка при экспорте заметок для user_id {user_id}: {e}")
        bot.reply_to(message, "Произошла ошибка при создании файла экспорта.")
    finally:
        if os.path.exists(file_path):
            os.remove(file_path)

@bot.message_handler(commands=['stats'])
def note_stats(message):
    user_id = message.from_user.id
    # Вызываем новую функцию для получения еженедельной статистики
    stats = get_weekly_stats(user_id)

    created_count = stats.get('create', 0)
    deleted_count = stats.get('delete', 0)

    if created_count == 0 and deleted_count == 0:
        bot.reply_to(message, "За последнюю неделю у вас не было активности. Пора это исправить!")
        return

    current_notes_count = len(list_all_notes(user_id))

    BAR_CHAR = '█'
    MAX_BAR_LENGTH = 20

    max_val = max(created_count, deleted_count, 1) # Используем 1, чтобы избежать деления на ноль

    created_bar = BAR_CHAR * int((created_count / max_val) * MAX_BAR_LENGTH)
    deleted_bar = BAR_CHAR * int((deleted_count / max_val) * MAX_BAR_LENGTH)

    # Обновляем заголовок и текст ответа
    response_text = (
        f"📊 **Еженедельная статистика активности** (за 7 дней)\n\n"
        f"`Создано : {created_count:<3} {created_bar}`\n"
        f"`Удалено : {deleted_count:<3} {deleted_bar}`\n\n"
        f"Всего заметок сейчас: **{current_notes_count}**"
    )

    bot.reply_to(message, response_text, parse_mode='Markdown')



if __name__ == "__main__":
    print("Бот запускается...")
    bot.infinity_polling(skip_pending=True)