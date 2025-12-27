import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from handlers.payments import router as payments_router

from config import BOT_TOKEN
from database.database import init_db
from handlers.start import router as start_router
from handlers.city_metro import router as city_metro_router
from handlers.main_menu import router as main_menu_router
from handlers.products import router as products_router

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

async def main():
    # Инициализация бота
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher(storage=MemoryStorage())
    
    # Инициализация БД
    await init_db()
    
    # Регистрация роутеров
    dp.include_router(start_router)
    dp.include_router(city_metro_router)
    dp.include_router(products_router)  
    dp.include_router(main_menu_router)
    dp.include_router(payments_router) 
    
    # Запуск бота
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())