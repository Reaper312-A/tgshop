from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardButton

router = Router()

# Здесь в будущем можно добавить:
# 1. Отображение товаров с пагинацией
# 2. Добавление товаров в корзину
# 3. Фильтрация товаров
# 4. Поиск товаров
# 5. Отзывы и рейтинги

# Пример структуры для будущих товаров:
"""
products = [
    {
        "id": 1,
        "name": "Blue Dream",
        "category": "weed",
        "subcategory": "buds",
        "price": 1500,
        "currency": "RUB",
        "description": "Сорт с ягодным ароматом",
        "quantity": 10
    },
    # ... другие товары
]
"""