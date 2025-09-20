import os
import telebot
from telebot import types

from log import setup_logging
from dotenv import load_dotenv

logger = setup_logging()
load_dotenv()

def make_main_Kb()->types.ReplyKeyboardMarkup:
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row("/help", "Сумма", "/hide")
    return kb

TOKEN = os.getenv("TOKEN")
if not TOKEN:
    logger.error("Токен не найден в .env файле")
    raise RuntimeError(" .env =5F TOKEN")

bot = telebot.TeleBot(TOKEN)
logger.info("Бот инициализирован")


def parse_ints_from_text(message):
    parts = message.split()
    numbers = []

    for p in parts[:]:
        if p.isdigit(): # только положительные целые
            numbers.append(int(p))

    return numbers


def on_sum_numbers(m: types.Message) -> None:
    logger.info(f"Обработка суммы чисел от пользователя {m.from_user.id}")
    nums = parse_ints_from_text(m.text)
    if not nums:
        logger.warning(f"Числа не найдены в сообщении: {m.text}")
        bot.reply_to(m, "Не вижу чисел. Пример: 2 3 10")
    else:
        logger.info(f"Вычислена сумма: {sum(nums)} для чисел: {nums}")
        bot.reply_to(m, f"Сумма: {sum(nums)}")


@bot.message_handler(commands=["start", "help"])
def start_help(m: types.Message) -> None:
    logger.info(f"Обработка команды {m.text} от пользователя {m.from_user.id}")
    bot.send_message(
        m.chat.id,
        "Привет! Доступно: /about, /sum, /echo, /confirm\n"
        "Или воспользуйтесь кнопками ниже.",
        reply_markup=make_main_Kb()
    )

@bot.message_handler(commands=['start'])
def start(message):
    logger.info(f"Команда start от пользователя {message.from_user.id}")
    bot.reply_to(message, "Привет! Я твой первый бот! напиши /help")

@bot.message_handler(commands=['help'])
def help_cmd(message):
    logger.info(f"Команда help от пользователя {message.from_user.id}")
    bot.reply_to(message, "/start - начать\n/help - помощь\n/about - о боте")

@bot.message_handler(commands=['about'])
def about_cmd(message):
    logger.info(f"Команда about от пользователя {message.from_user.id}")
    bot.reply_to(message, "Этот бот находится в стадии разработки. Следите за обновлениями!\nАвтор: Михайлова Р.А.\nВерсия: 0.0.1")

@bot.message_handler(commands=['ping'])
def ping_cmd(message):
    logger.info(f"Команда ping от пользователя {message.from_user.id}")
    bot.reply_to(message, "pong")

@bot.message_handler(commands=['sum'])
def cmd_sum(message):
    logger.info(f"Команда sum от пользователя {message.from_user.id}")
    parts = message.text.split()
    numbers = []

    for p in parts[1:]:
        if p.isdigit(): # только положительные целые
            numbers.append(int(p))

    if not numbers:
        logger.warning(f"Числа не найдены в команде sum: {message.text}")
        bot.reply_to(message, "Напиши числа: /sum 2 3 10")
    else:
        logger.info(f"Вычислена сумма: {sum(numbers)} для чисел: {numbers}")
        bot.reply_to(message, f"Сумма: {sum(numbers)}")

@bot.message_handler(func=lambda m: m.text == "Сумма")
def kb_sum(m):
    logger.info(f"Кнопка 'Сумма' от пользователя {m.from_user.id}")
    bot.send_message(m.chat.id, "Введи числа через пробел или запятую:")
    bot.register_next_step_handler(m, on_sum_numbers)

@bot.message_handler(commands=['hide'])
def hide_kb(m):
    logger.info(f"Команда hide от пользователя {m.from_user.id}")
    rm = types.ReplyKeyboardRemove()
    bot.send_message(m.chat.id, "Спрятал клавиатуру.", reply_markup=rm)

@bot.message_handler(commands=['confirm'])
def confirm_cmd(m):
    logger.info(f"Команда confirm от пользователя {m.from_user.id}")
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("Дa", callback_data="confirm:yes"),
           types.InlineKeyboardButton("Нет", callback_data="confirm:no"))
    bot.send_message(m.chat.id, "Подтвердить действие?", reply_markup=kb)

@bot.callback_query_handler(func=lambda c: c.data.startswith("confirm:"))
def on_confirm(c): # Извлекаем выбор пользователя
    choice = c.data.split(":", 1)[1]
    logger.info(f"Обработка callback: {c.data} от пользователя {c.from_user.id}")
    bot.answer_callback_query(c.id, "Принято")
    bot.edit_message_reply_markup(c.message.chat.id, c.message.message_id, reply_markup=None)
    bot.send_message(c.message.chat.id, "Готово!" if choice == "yes" else "Отменено.")


if __name__ == "__main__":
    logger.info("Запуск бота...")
    try:
        bot.infinity_polling(skip_pending=True)
    except Exception as e:
        logger.error(f"Ошибка при работе бота: {e}")
        raise