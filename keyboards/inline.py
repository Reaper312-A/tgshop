from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from config import CITIES, get_metro_stations_for_city

def get_start_keyboard(user_city: str = None, user_metro: str = None):
    """Клавиатура для выбора города и метро"""
    builder = InlineKeyboardBuilder()
    
    # Кнопка города
    city_text = user_city if user_city else "Город"
    builder.add(InlineKeyboardButton(
        text=f"📍 {city_text}",
        callback_data="select_city"
    ))
    
    # Кнопка метро/района
    metro_text = user_metro[:12] + "..." if user_metro and len(user_metro) > 12 else user_metro
    metro_text = metro_text if metro_text else "Район/Метро"
    builder.add(InlineKeyboardButton(
        text=f"🏘 {metro_text}",
        callback_data="select_metro"
    ))
    
    # Кнопка далее (только если выбраны и город и метро)
    if user_city and user_metro:
        builder.add(InlineKeyboardButton(
            text="✅ Далее",
            callback_data="start_main_menu"
        ))
    
    builder.adjust(2, 1)
    return builder.as_markup()

def get_cities_keyboard():
    """Клавиатура выбора города"""
    builder = InlineKeyboardBuilder()
    
    for city in CITIES:
        builder.add(InlineKeyboardButton(
            text=city,
            callback_data=f"city_{city}"
        ))
    
    builder.add(InlineKeyboardButton(
        text="◀️ Назад",
        callback_data="back_to_start"
    ))
    
    builder.adjust(1)
    return builder.as_markup()

def get_metro_keyboard(city: str, page: int = 0, items_per_page: int = 10):
    """Клавиатура выбора метро/района с пагинацией для конкретного города"""
    
    # Получаем станции метро/районы для выбранного города
    locations = get_metro_stations_for_city(city)
    
    # Расчет индексов для текущей страницы
    start_idx = page * items_per_page
    end_idx = start_idx + items_per_page
    current_page_locations = locations[start_idx:end_idx]
    
    # Определяем заголовок в зависимости от города
    if city in ["Москва", "СПБ"]:
        location_type = "станцию метро"
    else:
        location_type = "район"
    
    # Создаем клавиатуру
    keyboard = []
    
    # Заголовок с инструкцией
    title = f"Выберите {location_type} ({city}):"
    
    # Добавляем кнопки станций/районов
    for location in current_page_locations:
        keyboard.append([InlineKeyboardButton(
            text=location,
            callback_data=f"metro_{location}"
        )])
    
    # Кнопки навигации
    nav_row = []
    
    if page > 0:
        nav_row.append(InlineKeyboardButton(
            text="◀️",
            callback_data=f"metro_page_{page-1}"
        ))
    
    nav_row.append(InlineKeyboardButton(
        text="Назад",
        callback_data="back_to_start"
    ))
    
    if end_idx < len(locations):
        nav_row.append(InlineKeyboardButton(
            text="▶️",
            callback_data=f"metro_page_{page+1}"
        ))
    
    keyboard.append(nav_row)
    
    return title, InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_main_menu_keyboard():
    """Главное меню"""
    builder = InlineKeyboardBuilder()
    
    menu_items = [
        ("🛍 Каталог", "catalog"),
        ("📦 Мои заказы", "my_orders"),
        ("👤 Профиль", "profile"),
        ("📍 Город", "change_city"),
        ("🏪 О магазине", "about"),
        ("📞 Поддержка", "support"),
    ]
    
    for text, callback_data in menu_items:
        builder.add(InlineKeyboardButton(
            text=text,
            callback_data=callback_data
        ))
    
    builder.adjust(2, 2, 1, 1)
    return builder.as_markup()

def get_catalog_keyboard():
    """Каталог товаров"""
    builder = InlineKeyboardBuilder()
    
    catalog_items = [
        ("🌿 Марихуана", "category_weed"),
        ("🔧 Работа", "category_job"),
        ("🥊 Спортики/пробив", "category_sports"),
    ]
    
    for text, callback_data in catalog_items:
        builder.add(InlineKeyboardButton(
            text=text,
            callback_data=callback_data
        ))
    
    builder.add(InlineKeyboardButton(
        text="◀️ Назад",
        callback_data="back_to_main_menu"
    ))
    
    builder.adjust(1, 1, 1)
    return builder.as_markup()

def get_weed_subcategories_keyboard():
    """Подкатегории марихуаны"""
    builder = InlineKeyboardBuilder()
    
    subcategories = [
        ("🌿 Шишки", "subcat_buds"),
        ("🍫 Гашиш", "subcat_hash"),
        ("💧 Масло/Концентраты", "subcat_oil"),
        ("🍪 Ganjafood", "subcat_food"),
        ("◀️ Назад", "back_to_catalog"),
    ]
    
    for text, callback_data in subcategories:
        builder.add(InlineKeyboardButton(
            text=text,
            callback_data=callback_data
        ))
    
    builder.adjust(1)
    return builder.as_markup()


def get_job_subcategories_keyboard():
    """Подкатегории работы"""
    builder = InlineKeyboardBuilder()
    
    subcategories = [
        ("🚚 Курьер", "subcat_courier"),
        ("🚛 Перевозчик", "subcat_transport"),
        ("💻 Модератор", "subcat_moderator"),
        ("💪 Спортик", "subcat_sportik_job"),
        ("◀️ Назад", "back_to_catalog"),
    ]
    
    for text, callback_data in subcategories:
        builder.add(InlineKeyboardButton(
            text=text,
            callback_data=callback_data
        ))
    
    builder.adjust(1)
    return builder.as_markup()

def get_sports_subcategories_keyboard():
    """Подкатегории спортиков/пробива"""
    builder = InlineKeyboardBuilder()
    
    subcategories = [
        ("💊 Спортики", "subcat_sport_pills"),
        ("🔍 Пробить человека", "subcat_search_person"),
        ("◀️ Назад", "back_to_catalog"),
    ]
    
    for text, callback_data in subcategories:
        builder.add(InlineKeyboardButton(
            text=text,
            callback_data=callback_data
        ))
    
    builder.adjust(1)
    return builder.as_markup()

def get_back_keyboard(target: str = "main_menu"):
    """Клавиатура с кнопкой назад"""
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(
        text="◀️ Назад",
        callback_data=f"back_to_{target}"
    ))
    return builder.as_markup()

def payment_keyboard(payment_url: str) -> InlineKeyboardMarkup:
    """
    Клавиатура оплаты с кнопкой инструкции
    """
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="💳 Оплатить",
                    url=payment_url
                )
            ],
            [
                InlineKeyboardButton(
                    text="📖 Инструкция по оплате",
                    callback_data="payment_instruction"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🔙 В меню",
                    callback_data="main_menu"
                )
            ]
        ]
    )