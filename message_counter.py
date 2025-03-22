import json
import os
from datetime import datetime
import logging

# Путь к файлу, где будут храниться данные о сообщениях
COUNTER_FILE = 'message_counter.json'

def load_counters():
    """Загружает счетчики сообщений из файла."""
    if not os.path.exists(COUNTER_FILE):
        logging.info("Создание нового файла счетчиков.")
        return {}
    try:
        with open(COUNTER_FILE, 'r') as file:
            counters = json.load(file)
            logging.info(f"Загружены счетчики: {counters}")
            return counters
    except json.JSONDecodeError as e:
        logging.error(f"Ошибка при чтении файла счетчиков: {e}")
        return {}

def save_counters(counters):
    """Сохраняет счетчики сообщений в файл."""
    try:
        with open(COUNTER_FILE, 'w') as file:
            json.dump(counters, file)
            logging.info(f"Сохранены счетчики: {counters}")
    except IOError as e:
        logging.error(f"Ошибка при сохранении счетчиков в файл: {e}")

def update_message_counter(user_id):
    """Обновляет счетчик сообщений для пользователя."""
    counters = load_counters()
    today = datetime.now().strftime('%Y-%m-%d')

    if user_id not in counters:
        counters[user_id] = {'date': today, 'count': 0}
        logging.info(f"Создан новый счетчик для пользователя {user_id}.")

    # Если дата изменилась, сбросить счетчик
    if counters[user_id]['date'] != today:
        counters[user_id] = {'date': today, 'count': 0}
        logging.info(f"Счетчик для пользователя {user_id} сброшен.")

    # Увеличить счетчик
    counters[user_id]['count'] += 1
    logging.info(f"Счетчик для пользователя {user_id} увеличен. Текущее значение: {counters[user_id]['count']}")
    save_counters(counters)

def get_message_count(user_id):
    """Возвращает количество сообщений, отправленных пользователем за сегодня."""
    counters = load_counters()
    count = counters.get(user_id, {'count': 0})['count']
    logging.info(f"Счетчик для пользователя {user_id}: {count}")
    return count

def reset_daily_counters():
    """Сбрасывает счетчики сообщений для всех пользователей."""
    counters = load_counters()
    today = datetime.now().strftime('%Y-%m-%d')
    for user_id in counters:
        counters[user_id] = {'date': today, 'count': 0}
    logging.info("Все счетчики сброшены.")
    save_counters(counters)
