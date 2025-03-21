import json
import os

# Путь к файлу, где будут храниться данные о пользователях
USERS_FILE = 'users.json'

def load_users():
    """Загружает данные о пользователях из файла."""
    if not os.path.exists(USERS_FILE):
        return {}
    with open(USERS_FILE, 'r') as file:
        return json.load(file)

def save_users(users):
    """Сохраняет данные о пользователях в файл."""
    with open(USERS_FILE, 'w') as file:
        json.dump(users, file)

def add_user(user_id, username):
    """Добавляет нового пользователя."""
    users = load_users()
    if user_id not in users:
        users[user_id] = username
        save_users(users)

def get_all_users():
    """Возвращает список всех пользователей."""
    users = load_users()
    return users
