from typing import Dict, Set

# Глобальные переменные для хранения информации о пользователях
users: Set[int] = set()
user_data: Dict[int, Dict] = {}

def add_user(user_id: int, username: str = None, first_name: str = None, last_name: str = None):
    """Добавляет пользователя в статистику."""
    users.add(user_id)
    
    if user_id not in user_data:
        user_data[user_id] = {
            "username": username,
            "first_name": first_name,
            "last_name": last_name
        }

def get_user_stats():
    """Возвращает статистику пользователей."""
    return {
        "count": len(users),
        "users": user_data
    }
