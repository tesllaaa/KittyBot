import os
from dotenv import load_dotenv
import telebot
import time
from db import init_db, add_note, list_notes, update_note, delete_note, find_notes, list_all_notes, get_weekly_stats

# Загрузка переменных окружения
load_dotenv()
TOKEN = os.getenv("TOKEN")
if not TOKEN:
    raise RuntimeError("В .env файле нет TOKEN")

bot = telebot.TeleBot(TOKEN)

# Инициализация базы данных при запуске
init_db()

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