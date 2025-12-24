from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.filters import Command

from database.database import get_user_city, get_user_metro, get_user_balance
from keyboards.inline import (
    get_main_menu_keyboard, 
    get_start_keyboard, 
    get_back_keyboard,
    get_catalog_keyboard,
    get_weed_subcategories_keyboard,
    get_job_subcategories_keyboard,
    get_sports_subcategories_keyboard
)

router = Router()

@router.callback_query(F.data == "start_main_menu")
async def start_main_menu(callback: CallbackQuery):
    """Переход в главное меню"""
    await callback.message.edit_text(
        "🏠 Главное меню\n\n"
        "Выберите раздел:",
        reply_markup=get_main_menu_keyboard()
    )
    await callback.answer()

@router.callback_query(F.data == "back_to_main_menu")
async def back_to_main_menu(callback: CallbackQuery):
    """Возврат в главное меню"""
    await callback.message.edit_text(
        "🏠 Главное меню\n\n"
        "Выберите раздел:",
        reply_markup=get_main_menu_keyboard()
    )
    await callback.answer()

@router.callback_query(F.data == "change_city")
async def change_city(callback: CallbackQuery):
    """Изменение города/метро из главного меню"""
    city = await get_user_city(callback.from_user.id)
    metro = await get_user_metro(callback.from_user.id)
    
    await callback.message.edit_text(
        "🔄 Изменение города и метро\n\n"
        "Выберите новые настройки:",
        reply_markup=get_start_keyboard(city, metro)
    )
    await callback.answer()

@router.callback_query(F.data == "catalog")
async def show_catalog(callback: CallbackQuery):
    """Показ каталога"""
    await callback.message.edit_text(
        "🛍 Каталог товаров\n\n"
        "Выберите категорию:",
        reply_markup=get_catalog_keyboard()
    )
    await callback.answer()

@router.callback_query(F.data == "category_weed")
async def show_weed_category(callback: CallbackQuery):
    """Показ категории марихуаны"""
    await callback.message.edit_text(
        "🌿 Марихуана\n\n"
        "Выберите подкатегорию:",
        reply_markup=get_weed_subcategories_keyboard()
    )
    await callback.answer()


@router.callback_query(F.data == "category_job")
async def show_job_category(callback: CallbackQuery):
    """Показ категории работы"""
    await callback.message.edit_text(
        "🔧 Работа\n\n"
        "Выберите подкатегорию:",
        reply_markup=get_job_subcategories_keyboard()
    )
    await callback.answer()

@router.callback_query(F.data == "category_sports")
async def show_sports_category(callback: CallbackQuery):
    """Показ категории спортиков/пробива"""
    await callback.message.edit_text(
        "🥊 Спортики/пробив\n\n"
        "Выберите подкатегорию:",
        reply_markup=get_sports_subcategories_keyboard()
    )
    await callback.answer()



@router.callback_query(F.data == "back_to_catalog")
async def back_to_catalog(callback: CallbackQuery):
    """Возврат в каталог"""
    await callback.message.edit_text(
        "🛍 Каталог товаров\n\n"
        "Выберите категорию:",
        reply_markup=get_catalog_keyboard()
    )
    await callback.answer()

@router.callback_query(F.data == "my_orders")
async def show_orders(callback: CallbackQuery):
    """Показ заказов"""
    await callback.message.edit_text(
        "📦 Мои заказы\n\n"
        "У вас пока нет заказов.\n"
        "Совершите первую покупку!",
        reply_markup=get_back_keyboard("main_menu")
    )
    await callback.answer()

@router.callback_query(F.data == "profile")
async def show_profile(callback: CallbackQuery):
    """Показ профиля"""
    city = await get_user_city(callback.from_user.id)
    metro = await get_user_metro(callback.from_user.id)
    
    # Получаем баланс (всегда нули)
    balance = await get_user_balance(callback.from_user.id)
    
    await callback.message.edit_text(
        f"👤 Ваш профиль\n\n"
        f"🆔 ID: {callback.from_user.id}\n"
        f"👤 Имя: {callback.from_user.first_name or 'Не указано'}\n"
        f"📍 Город: {city if city else 'Не выбран'}\n"
        f"🚇 Метро: {metro if metro else 'Не выбрано'}\n\n"
        f"💰 Баланс:\n"
        f"  ₿ BTC: {balance['btc']:.4f}\n"
        f"  💵 UST: {balance['ust']:.2f}\n"
        f"  ₽ RUB: {balance['rub']:,}\n"
        f"  ⭐ Stars: {balance['stars']}",
        reply_markup=get_back_keyboard("main_menu")
    )
    await callback.answer()

@router.callback_query(F.data == "about")
async def show_about(callback: CallbackQuery):
    """Информация о магазине"""
    await callback.message.edit_text(
        "🏪 О нашем магазине\n\n"
        "Это игровой магазин для симуляции торговли!\n\n"
        "👥 Игроков онлайн: 1,245\n"
        "🎮 Создано: 2024\n"
        "⭐ Рейтинг: 4.9/5\n",
        reply_markup=get_back_keyboard("main_menu")
    )
    await callback.answer()

@router.callback_query(F.data == "support")
async def show_support(callback: CallbackQuery):
    """Поддержка"""
    await callback.message.edit_text(
        "📞 Поддержка\n\n"
        "По всем вопросам игры обращайтесь:\n\n"
        "📱 Телеграм: @gamesupport\n"
        "💬 Чат: @gamechat\n"
        "🕒 Онлайн: 24/7",
        reply_markup=get_back_keyboard("main_menu")
    )
    await callback.answer()