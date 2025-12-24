from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart

from database.database import get_or_create_user, get_user_city, get_user_metro
from keyboards.inline import get_start_keyboard

router = Router()

@router.message(CommandStart())
async def cmd_start(message: Message):
    """Обработка команды /start"""
    # Получаем или создаем пользователя
    user = await get_or_create_user(message.from_user.id)
    
    # Получаем текущие настройки пользователя
    city = await get_user_city(message.from_user.id)
    metro = await get_user_metro(message.from_user.id)
    
    await message.answer(
        "👋 Добро пожаловать!\n\n"
        "Пожалуйста, выберите ваш город и район/станцию метро:",
        reply_markup=get_start_keyboard(city, metro)
    )

@router.callback_query(F.data == "back_to_start")
async def back_to_start(callback: CallbackQuery):
    """Возврат к начальному меню"""
    city = await get_user_city(callback.from_user.id)
    metro = await get_user_metro(callback.from_user.id)
    
    await callback.message.edit_text(
        "👋 Добро пожаловать!\n\n"
        "Пожалуйста, выберите ваш город и район/станцию метро:",
        reply_markup=get_start_keyboard(city, metro)
    )
    await callback.answer()