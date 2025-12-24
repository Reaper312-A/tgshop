import aiosqlite
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

DB_NAME = "database/bot_database.db"

async def init_db():
    """Инициализация базы данных"""
    async with aiosqlite.connect(DB_NAME) as db:
        # Таблица пользователей (без балансов)
        await db.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_id INTEGER UNIQUE,
                city TEXT,
                metro TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        await db.commit()
        logger.info("База данных инициализирована")
        
        # Таблица настроек пользователей
        await db.execute('''
            CREATE TABLE IF NOT EXISTS user_settings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                city TEXT,
                metro TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        # Таблица товаров (оставим на будущее)
        await db.execute('''
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                category TEXT,
                subcategory TEXT,
                price REAL,
                currency TEXT,
                description TEXT,
                quantity INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        await db.commit()
        logger.info("База данных инициализирована")

async def get_or_create_user(telegram_id: int):
    """Получить или создать пользователя"""
    async with aiosqlite.connect(DB_NAME) as db:
        # Проверяем существование пользователя
        cursor = await db.execute(
            "SELECT id, telegram_id, city, metro FROM users WHERE telegram_id = ?",
            (telegram_id,)
        )
        user = await cursor.fetchone()
        
        if user:
            return {
                "id": user[0],
                "telegram_id": user[1],
                "city": user[2],
                "metro": user[3]
            }
        else:
            # Создаем нового пользователя
            await db.execute(
                "INSERT INTO users (telegram_id) VALUES (?)",
                (telegram_id,)
            )
            await db.commit()
            
            # Получаем созданного пользователя
            cursor = await db.execute(
                "SELECT id, telegram_id, city, metro FROM users WHERE telegram_id = ?",
                (telegram_id,)
            )
            new_user = await cursor.fetchone()
            return {
                "id": new_user[0],
                "telegram_id": new_user[1],
                "city": new_user[2],
                "metro": new_user[3]
            }

async def update_user_city(telegram_id: int, city: str):
    """Обновить город пользователя"""
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            "UPDATE users SET city = ?, updated_at = CURRENT_TIMESTAMP WHERE telegram_id = ?",
            (city, telegram_id)
        )
        await db.commit()

async def update_user_metro(telegram_id: int, metro: str):
    """Обновить станцию метро пользователя"""
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            "UPDATE users SET metro = ?, updated_at = CURRENT_TIMESTAMP WHERE telegram_id = ?",
            (metro, telegram_id)
        )
        await db.commit()

async def get_user_city(telegram_id: int):
    """Получить город пользователя"""
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute(
            "SELECT city FROM users WHERE telegram_id = ?",
            (telegram_id,)
        )
        result = await cursor.fetchone()
        return result[0] if result else None

async def get_user_metro(telegram_id: int):
    """Получить станцию метро пользователя"""
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute(
            "SELECT metro FROM users WHERE telegram_id = ?",
            (telegram_id,)
        )
        result = await cursor.fetchone()
        return result[0] if result else None

async def get_user_balance(telegram_id: int):
    """Получить баланс пользователя (всегда нули)"""
    return {
        "btc": 0.0,
        "ust": 0.0,
        "rub": 0,
        "stars": 0
    }