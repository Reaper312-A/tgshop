from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext

from database.database import update_user_city, update_user_metro, get_user_city, get_user_metro
from keyboards.inline import get_start_keyboard, get_cities_keyboard, get_metro_keyboard
from config import CITIES

router = Router()

# Словарь для хранения текущего города при выборе метро
user_current_city = {}

@router.callback_query(F.data == "select_city")
async def select_city(callback: CallbackQuery):
    """Выбор города"""
    await callback.message.edit_text(
        "🏙 Выберите ваш город:",
        reply_markup=get_cities_keyboard()
    )
    await callback.answer()

@router.callback_query(F.data.startswith("city_"))
async def city_chosen(callback: CallbackQuery):
    """Город выбран"""
    city = callback.data.split("_", 1)[1]
    
    # Сохраняем выбранный город для этого пользователя
    user_current_city[callback.from_user.id] = city
    
    # Обновляем город в БД
    await update_user_city(callback.from_user.id, city)
    
    # Получаем обновленные данные
    city = await get_user_city(callback.from_user.id)
    metro = await get_user_metro(callback.from_user.id)
    
    # Определяем текст кнопки в зависимости от города
    if city in ["Москва", "СПБ"]:
        location_text = "Метро"
    else:
        location_text = "Район"
    
    await callback.message.edit_text(
        f"✅ Город выбран: {city}\n\n"
        f"Теперь выберите {location_text.lower()}:",
        reply_markup=get_start_keyboard(city, metro)
    )
    await callback.answer()

@router.callback_query(F.data == "select_metro")
async def select_metro(callback: CallbackQuery):
    """Выбор метро/района"""
    # Получаем текущий город пользователя
    user_id = callback.from_user.id
    city = user_current_city.get(user_id)
    
    if not city:
        # Если город не выбран, получаем из БД
        city = await get_user_city(user_id)
        if not city:
            # Если города нет в БД, просим выбрать сначала город
            await callback.message.edit_text(
                "⚠️ Сначала выберите город!",
                reply_markup=get_cities_keyboard()
            )
            await callback.answer()
            return
    
    # Получаем заголовок и клавиатуру
    title, keyboard = get_metro_keyboard(city=city, page=0)
    
    await callback.message.edit_text(
        title,
        reply_markup=keyboard
    )
    await callback.answer()

@router.callback_query(F.data.startswith("metro_page_"))
async def metro_page_change(callback: CallbackQuery):
    """Смена страницы выбора метро/района"""
    # Получаем текущий город пользователя
    user_id = callback.from_user.id
    city = user_current_city.get(user_id)
    
    if not city:
        # Если город не выбран, получаем из БД
        city = await get_user_city(user_id)
        if not city:
            await callback.answer("Сначала выберите город!")
            return
    
    page = int(callback.data.split("_")[2])
    
    # Получаем заголовок и клавиатуру
    title, keyboard = get_metro_keyboard(city=city, page=page)
    
    await callback.message.edit_text(
        title,
        reply_markup=keyboard
    )
    await callback.answer()

@router.callback_query(F.data.startswith("metro_"))
async def metro_chosen(callback: CallbackQuery):
    """Станция метро/район выбрана"""
    # Извлекаем название станции/района
    parts = callback.data.split("_", 1)
    if len(parts) > 1:
        metro = parts[1]
    else:
        metro = callback.data
    
    # Обновляем метро/район в БД
    await update_user_metro(callback.from_user.id, metro)
    
    # Получаем обновленные данные
    city = await get_user_city(callback.from_user.id)
    metro_name = await get_user_metro(callback.from_user.id)
    
    # Определяем что выбрано
    if city in ["Москва", "СПБ"]:
        location_type = "Станция метро"
        location_emoji = "🚇"
    else:
        location_type = "Район"
        location_emoji = "🏘"
    
    await callback.message.edit_text(
        f"✅ {location_type} выбрана: {metro_name}\n\n"
        f"📍 Город: {city}\n"
        f"{location_emoji} {location_type}: {metro_name}\n\n"
        "Проверьте ваш выбор:",
        reply_markup=get_start_keyboard(city, metro_name)
    )
    await callback.answer()