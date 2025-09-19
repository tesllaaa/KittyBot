import os
import telebot

from log import setup_logging
from dotenv import load_dotenv

logger = setup_logging()
load_dotenv()

TOKEN = os.getenv("TOKEN")
if not TOKEN:
    raise RuntimeError(" .env =5F TOKEN")
bot = telebot.TeleBot(TOKEN)
@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, "Привет! Я твой первый бот! напиши /help")
@bot.message_handler(commands=['help'])
def help_cmd(message):
    bot.reply_to(message, "/start - начать\n/help - помощь\n/about - о боте")
@bot.message_handler(commands=['about'])
def about_cmd(message):
    bot.reply_to(message, "Этот бот находится в стадии разработки. Следите за обновлениями!\nАвтор: Михайлова Р.А.\nВерсия: 0.0.1")
@bot.message_handler(commands=['ping'])
def ping_cmd(message):
    bot.reply_to(message, "pong")

if __name__ == "__main__":
    bot.infinity_polling(skip_pending=True)
