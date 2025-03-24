import datetime
from typing import Dict

# Глобальные переменные для хранения статистики
total_messages = 0
today_messages = 0
messages_per_day: Dict[str, int] = {}

def increment_message_count():
    """Увеличивает счетчики сообщений."""
    global total_messages, today_messages
    
    total_messages += 1
    
    today = datetime.date.today().isoformat()
    if today not in messages_per_day:
        messages_per_day[today] = 0
    messages_per_day[today] += 1
    today_messages = messages_per_day[today]

def get_message_stats():
    """Возвращает статистику сообщений."""
    return {
        "total": total_messages,
        "today": today_messages
    }
