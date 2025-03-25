import sqlite3
from datetime import datetime

def init_db():
    conn = sqlite3.connect("bot_stats.db")
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            date TEXT PRIMARY KEY,
            count INTEGER DEFAULT 0
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            first_name TEXT,
            last_name TEXT,
            last_interaction TEXT
        )
    """)
    
    conn.commit()
    conn.close()

def increment_message_count():
    today = datetime.now().strftime("%Y-%m-%d")
    conn = sqlite3.connect("bot_stats.db")
    cursor = conn.cursor()
    
    cursor.execute(
        "INSERT OR IGNORE INTO messages (date, count) VALUES (?, 0)",
        (today,)
    )
    cursor.execute(
        "UPDATE messages SET count = count + 1 WHERE date = ?",
        (today,)
    )
    
    conn.commit()
    conn.close()

def add_user(user_id, username=None, first_name=None, last_name=None):
    conn = sqlite3.connect("bot_stats.db")
    cursor = conn.cursor()
    
    cursor.execute(
        """
        INSERT OR REPLACE INTO users 
        (user_id, username, first_name, last_name, last_interaction)
        VALUES (?, ?, ?, ?, ?)
        """,
        (user_id, username, first_name, last_name, datetime.now().isoformat())
    )
    
    conn.commit()
    conn.close()

def get_message_stats():
    conn = sqlite3.connect("bot_stats.db")
    cursor = conn.cursor()
    
    cursor.execute("SELECT SUM(count) FROM messages")
    total = cursor.fetchone()[0] or 0
    
    today = datetime.now().strftime("%Y-%m-%d")
    cursor.execute("SELECT count FROM messages WHERE date = ?", (today,))
    today_count = cursor.fetchone()
    today_count = today_count[0] if today_count else 0
    
    conn.close()
    return {"total": total, "today": today_count}

def get_user_stats():
    conn = sqlite3.connect("bot_stats.db")
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM users")
    count = cursor.fetchone()[0]
    
    cursor.execute("SELECT * FROM users")
    users = {
        row[0]: {
            "username": row[1],
            "first_name": row[2],
            "last_name": row[3]
        }
        for row in cursor.fetchall()
    }
    
    conn.close()
    return {"count": count, "users": users}

# Инициализация БД при импорте
init_db()
