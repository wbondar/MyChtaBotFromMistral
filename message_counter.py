import sqlite3
from datetime import datetime
import logging

# Путь к базе данных
DATABASE = 'message_counter.db'

def init_db():
    """Инициализирует базу данных."""
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS counters (
            user_id TEXT PRIMARY KEY,
            date TEXT,
            count INTEGER
        )
        ''')
        conn.commit()

def load_counters():
    """Загружает счетчики сообщений из базы данных."""
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT user_id, date, count FROM counters')
        counters = {row[0]: {'date': row[1], 'count': row[2]} for row in cursor.fetchall()}
        logging.info(f"Загружены счетчики: {counters}")
        return counters

def save_counters(counters):
    """Сохраняет счетчики сообщений в базу данных."""
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        for user_id, data in counters.items():
            cursor.execute('''
            INSERT OR REPLACE INTO counters (user_id, date, count)
            VALUES (?, ?, ?)
            ''', (user_id, data['date'], data['count']))
        conn.commit()
        logging.info(f"Сохранены счетчики: {counters}")

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

# Инициализация базы данных при первом запуске
init_db()
