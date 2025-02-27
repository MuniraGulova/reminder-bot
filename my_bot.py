import telebot
import threading
import datetime
import time
import json
import os

TOKEN = os.getenv("TOKEN")


bot = telebot.TeleBot(TOKEN)

# Файл для хранения задач
TASKS_FILE = 'tasks.json'

try:
    with open(TASKS_FILE, 'r', encoding='utf-8') as file:
        tasks = json.load(file)
except FileNotFoundError:
    tasks = {}

def save_tasks():
    with open(TASKS_FILE, 'w', encoding='utf-8') as file:
        json.dump(tasks, file, ensure_ascii=False)

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    bot.reply_to(message, "Привет! Я твой бот-напоминалка 📅.\n"
                          "Команды:\n"
                          "/add - добавить задачу\n"
                          "/tasks - список задач\n"
                          "/delete - удалить задачу")

@bot.message_handler(commands=['add'])
def add_task(message):
    msg = bot.reply_to(message, "Напиши задачу так: Описание;ЧЧ:ММ")
    bot.register_next_step_handler(msg, save_task, message.chat.id)

def save_task(message, chat_id):
    try:
        description, time_str = message.text.split(';')
        description, time_str = description.strip(), time_str.strip()

        if chat_id not in tasks:
            tasks[chat_id] = []

        tasks[chat_id].append({'description': description, 'time': time_str, 'notified': False})
        save_tasks()
        bot.send_message(chat_id, f"Задача добавлена: {description} в {time_str}")
    except:
        bot.send_message(chat_id, "Ошибка! Пиши: Описание;ЧЧ:ММ")

@bot.message_handler(commands=['tasks'])
def list_tasks(message):
    chat_id = message.chat.id
    if chat_id not in tasks or not tasks[chat_id]:
        bot.reply_to(message, "Задач пока нет.")
        return

    text = "\n".join([f"{i+1}. {t['description']} - {t['time']}" for i, t in enumerate(tasks[chat_id])])
    bot.reply_to(message, "Твои задачи:\n" + text)

@bot.message_handler(commands=['delete'])
def delete_task(message):
    chat_id = message.chat.id
    if chat_id not in tasks or not tasks[chat_id]:
        bot.reply_to(message, "Задач нет.")
        return

    text = "\n".join([f"{i+1}. {t['description']} - {t['time']}" for i, t in enumerate(tasks[chat_id])])
    msg = bot.reply_to(message, "Выбери номер задачи для удаления:\n" + text)
    bot.register_next_step_handler(msg, remove_task, chat_id)

def remove_task(message, chat_id):
    try:
        index = int(message.text) - 1
        if 0 <= index < len(tasks[chat_id]):
            deleted = tasks[chat_id].pop(index)
            save_tasks()
            bot.send_message(chat_id, f"Удалена задача: {deleted['description']}")
        else:
            bot.send_message(chat_id, "Неправильный номер.")
    except:
        bot.send_message(chat_id, "Ошибка. Пиши только номер.")

def check_reminders():
    while True:
        now = datetime.datetime.now().strftime("%H:%M")
        for chat_id, task_list in tasks.items():
            for task in task_list:
                if task['time'] == now and not task['notified']:
                    bot.send_message(chat_id, f"🔔 Напоминание: {task['description']}")
                    task['notified'] = True
        save_tasks()
        time.sleep(30)

threading.Thread(target=check_reminders, daemon=True).start()

bot.polling(none_stop=True)
