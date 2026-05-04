import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "nequi.db")

def get_conn():
    return sqlite3.connect(DB_PATH)

def init_db():
    conn = get_conn()
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        phone TEXT UNIQUE NOT NULL,
        name TEXT NOT NULL,
        pin TEXT NOT NULL,
        balance REAL DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS admins (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        telegram_id INTEGER UNIQUE NOT NULL,
        name TEXT
    )''')
    conn.commit()
    conn.close()

def add_admin(telegram_id, name):
    conn = get_conn()
    c = conn.cursor()
    try:
        c.execute("INSERT INTO admins (telegram_id, name) VALUES (?, ?)", (telegram_id, name))
        conn.commit()
        return True
    except:
        return False
    finally:
        conn.close()

def remove_admin(telegram_id):
    conn = get_conn()
    c = conn.cursor()
    c.execute("DELETE FROM admins WHERE telegram_id = ?", (telegram_id,))
    conn.commit()
    conn.close()

def is_admin(telegram_id):
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT id FROM admins WHERE telegram_id = ?", (telegram_id,))
    result = c.fetchone()
    conn.close()
    return result is not None

def get_admins():
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT telegram_id, name FROM admins")
    result = c.fetchall()
    conn.close()
    return result

def create_user(phone, name, pin, balance=0):
    conn = get_conn()
    c = conn.cursor()
    try:
        c.execute("INSERT INTO users (phone, name, pin, balance) VALUES (?, ?, ?, ?)", (phone, name, pin, balance))
        conn.commit()
        return True
    except:
        return False
    finally:
        conn.close()

def get_user(phone):
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE phone = ?", (phone,))
    result = c.fetchone()
    conn.close()
    return result

def get_all_users():
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT phone, name, balance FROM users ORDER BY created_at DESC")
    result = c.fetchall()
    conn.close()
    return result

def update_user_name(phone, name):
    conn = get_conn()
    c = conn.cursor()
    c.execute("UPDATE users SET name = ? WHERE phone = ?", (name, phone))
    conn.commit()
    conn.close()

def update_user_phone(old_phone, new_phone):
    conn = get_conn()
    c = conn.cursor()
    try:
        c.execute("UPDATE users SET phone = ? WHERE phone = ?", (new_phone, old_phone))
        conn.commit()
        return True
    except:
        return False
    finally:
        conn.close()

def update_balance(phone, balance):
    conn = get_conn()
    c = conn.cursor()
    c.execute("UPDATE users SET balance = ? WHERE phone = ?", (balance, phone))
    conn.commit()
    conn.close()

def delete_user(phone):
    conn = get_conn()
    c = conn.cursor()
    c.execute("DELETE FROM users WHERE phone = ?", (phone,))
    conn.commit()
    conn.close()

def save_token(phone, token):
    conn = get_conn()
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS tokens (
        phone TEXT PRIMARY KEY,
        token TEXT
    )''')
    c.execute("INSERT OR REPLACE INTO tokens (phone, token) VALUES (?, ?)", (phone, token))
    conn.commit()
    conn.close()

def get_phone_by_token(token):
    conn = get_conn()
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS tokens (
        phone TEXT PRIMARY KEY,
        token TEXT
    )''')
    c.execute("SELECT phone FROM tokens WHERE token = ?", (token,))
    result = c.fetchone()
    conn.close()
    return result[0] if result else None

def token_exists(token):
    return get_phone_by_token(token) is not None
