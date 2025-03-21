import json
import os
from datetime import datetime

# Путь к файлу, где будут храниться данные о сообщениях
COUNTER_FILE = 'message_counter.json'

def load_counters():
    """Загружает счетчики сообщений из файла."""
    if not os.path.exists(COUNTER_FILE):
        return {}
    with open(COUNTER_FILE, 'r') as file:
        return json.load(file)

def save_counters(counters):
    """Сохраняет счетчики сообщений в файл."""
    with open(COUNTER_FILE, 'w') as file:
        json.dump(counters, file)

def update_message_counter(user_id):
    """Обновляет счетчик сообщений для пользователя."""
    counters = load_counters()
    today = datetime.now().strftime('%Y-%m-%d')

    if user_id not in counters:
        counters[user_id] = {'date': today, 'count': 0}

    # Если дата изменилась, сбросить счетчик
    if counters[user_id]['date'] != today:
        counters[user_id] = {'date': today, 'count': 0}

    # Увеличить счетчик
    counters[user_id]['count'] += 1
    save_counters(counters)

def get_message_count(user_id):
    """Возвращает количество сообщений, отправленных пользователем за сегодня."""
    counters = load_counters()
    return counters.get(user_id, {'count': 0})['count']

def reset_daily_counters():
    """Сбрасывает счетчики сообщений для всех пользователей."""
    counters = load_counters()
    today = datetime.now().strftime('%Y-%m-%d')
    for user_id in counters:
        counters[user_id] = {'date': today, 'count': 0}
    save_counters(counters)
