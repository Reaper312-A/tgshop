from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from data.products import Product
from typing import List

def get_products_grid_keyboard(products: List[Product], page: int = 0, products_per_page: int = 4):
    """Клавиатура с сеткой товаров (4 товара на странице)"""
    
    start_idx = page * products_per_page
    end_idx = start_idx + products_per_page
    current_products = products[start_idx:end_idx]
    
    builder = InlineKeyboardBuilder()
    
    # Добавляем кнопки товаров (по 2 в ряд)
    for i in range(0, len(current_products), 2):
        row = []
        for j in range(2):
            if i + j < len(current_products):
                product = current_products[i + j]
                row.append(InlineKeyboardButton(
                    text=product.short_description,
                    callback_data=f"product_{product.id}"
                ))
        if row:
            builder.row(*row)
    
    # Кнопки навигации
    nav_buttons = []
    
    if page > 0:
        nav_buttons.append(InlineKeyboardButton(
            text="◀️",
            callback_data=f"products_page_{page-1}"
        ))
    
    # Индикатор страницы
    total_pages = (len(products) + products_per_page - 1) // products_per_page
    nav_buttons.append(InlineKeyboardButton(
        text=f"{page + 1}/{total_pages}",
        callback_data="current_page"
    ))
    
    if end_idx < len(products):
        nav_buttons.append(InlineKeyboardButton(
            text="▶️",
            callback_data=f"products_page_{page+1}"
        ))
    
    if nav_buttons:
        builder.row(*nav_buttons)
    
    # Кнопка назад
    builder.row(InlineKeyboardButton(
        text="◀️ Назад к подкатегориям",
        callback_data="back_to_subcategories"
    ))
    
    return builder.as_markup()

def get_product_detail_keyboard(product, category, subcategory):
    """Клавиатура для детального просмотра товара"""
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    
    # Основная кнопка покупки
    keyboard = [
        [
            InlineKeyboardButton(
                text=f"💰 Купить за {product.price} руб.",
                callback_data=f"buy_product_{product.id}"  # Изменено!
            )
        ],
        [
            InlineKeyboardButton(text="◀️ Назад", callback_data=f"back_to_products_{category}_{subcategory}"),
            InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")
        ]
    ]
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)
    
  #  builder.adjust(1)
   # return builder.as_markup()