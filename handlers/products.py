from aiogram import Router, F
from aiogram.types import CallbackQuery, InputMediaPhoto
from aiogram.fsm.context import FSMContext

from data.products import get_products_by_subcategory, get_product_by_id
from keyboards.products import get_products_grid_keyboard, get_product_detail_keyboard
from keyboards.inline import (
    get_weed_subcategories_keyboard,
    get_job_subcategories_keyboard,
    get_sports_subcategories_keyboard
)
from utils.photos import get_category_photo_file, get_product_photo_file
from utils.payments import CryptoPayment

crypto_pay = CryptoPayment()
router = Router()

# Храним состояние для каждого пользователя
user_product_pages = {}

async def show_products_page(callback: CallbackQuery, user_id: int, page: int = 0):
    """Показать страницу товаров с фото"""
    if user_id not in user_product_pages:
        await callback.answer("Сессия устарела, выберите категорию заново")
        return
    
    data = user_product_pages[user_id]
    products = data["products"]
    category = data["category"]
    subcategory = data["subcategory"]
    
    # Для категорий "job" и "sports" показываем просто список
    if category in ["job", "sports"]:
        await show_job_or_sports_list(callback, products, category, subcategory, page)
        return
    
    # Обновляем текущую страницу
    data["page"] = page
    
    # Определяем заголовок категории
    category_names = {
        "buds": "🌿 Шишки",
        "hash": "🍫 Гашиш",
        "oil": "💧 Масло/Вэйп",
        "food": "🍪 Cannafood",
        "courier": "🚚 Работа курьером",
        "transport": "🚛 Работа перевозчиком",
        "moderator": "💻 Работа модератором",
        "sportik": "💪 Работа спортиком",
        "player": "🥊 Спортик на соревнования",  # Изменено с "pills" на "player"
        "search": "🔍 Пробив человека",
    }
    
    # Для категории "all" показываем общее название
    if subcategory == "all":
        category_name = "🌿 Все товары"
    else:
        category_name = category_names.get(subcategory, "Товары")
    
    # Получаем фото категории
    # ДЛЯ ПОДКАТЕГОРИИ "ALL" ПОКАЗЫВАЕМ ФОТО ИЗ РАЗНЫХ ПОДКАТЕГОРИЙ
    if subcategory == "all":
        # Список всех подкатегорий в правильном порядке
        all_subcategories = ["buds", "hash", "oil", "food"]
        
        # Определяем, какую подкатегорию показывать на этой странице
        # Каждые 2 страницы меняем подкатегорию
        subcat_index = (page // 2) % len(all_subcategories)
        display_subcategory = all_subcategories[subcat_index]
        
        # Для разнообразия: если на странице есть товары конкретной подкатегории,
        # показываем фото этой подкатегории
        current_products = products[page*4:page*4+4] if page*4 < len(products) else []
        if current_products:
            # Пробуем определить доминирующую подкатегорию на странице
            subcats_on_page = [p.subcategory for p in current_products if hasattr(p, 'subcategory')]
            if subcats_on_page:
                # Берем самую частую подкатегорию на странице
                from collections import Counter
                most_common = Counter(subcats_on_page).most_common(1)
                if most_common:
                    display_subcategory = most_common[0][0]
    else:
        display_subcategory = subcategory
    
    # Получаем фото (используем page % 3 чтобы циклически проходить по фото)
    photo_page = (page % 3) + 1  # 1, 2, 3, 1, 2, 3...
    category_photo = get_category_photo_file(category, display_subcategory, photo_page - 1)
    
    # Формируем подпись
    total_pages = (len(products) + 3) // 4  # 4 товара на страницу
    caption = f"{category_name}\n\n"
    caption += f"Страница: {page + 1}/{total_pages}\n"
    
    # Для "Всех товаров" показываем информацию о подкатегориях
    if subcategory == "all":
        # Подсчитываем товары по подкатегориям
        from collections import Counter
        subcat_counts = Counter([p.subcategory for p in products if hasattr(p, 'subcategory')])
        
        caption += f"🌿 Шишки: {subcat_counts.get('buds', 0)} | "
        caption += f"🍫 Гашиш: {subcat_counts.get('hash', 0)} | "
        caption += f"💧 Масло: {subcat_counts.get('oil', 0)} | "
        caption += f"🍪 Еда: {subcat_counts.get('food', 0)}\n"
    else:
        caption += f"Найдено товаров: {len(products)}\n"
    
    caption += "Выберите товар для подробной информации:"
    
    # Если сообщение уже содержит фото, редактируем его
    if callback.message.photo:
        await callback.message.edit_media(
            media=InputMediaPhoto(
                media=category_photo,
                caption=caption
            ),
            reply_markup=get_products_grid_keyboard(products, page=page)
        )
    else:
        # Если фото нет, отправляем новое сообщение
        await callback.message.delete()
        await callback.message.answer_photo(
            photo=category_photo,
            caption=caption,
            reply_markup=get_products_grid_keyboard(products, page=page)
        )
    
    await callback.answer()

async def show_job_or_sports_list(callback: CallbackQuery, products, category: str, subcategory: str, page: int = 0):
    """Показать список работ или спортиков/пробива (без фото)"""
    if not products:
        from keyboards.inline import get_back_keyboard
        await callback.message.edit_text(
            "😔 В этой категории пока нет позиций.\n",
            reply_markup=get_back_keyboard("catalog")
        )
        await callback.answer()
        return
    
    # Показываем первый продукт из списка
    product = products[0] if products else None
    
    if product:
        text = f"*{product.name}*\n\n{product.description}"
        
        # Для работ (цена 0) показываем только кнопку "Назад"
        if category == "job":
            from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
            keyboard = InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(
                            text="◀️ Назад к подкатегориям",
                            callback_data="back_to_subcategories"
                        )
                    ]
                ]
            )
        else:
            # Для спортиков/пробива показываем кнопку покупки
            from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
            keyboard = InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(
                            text=f"💰 Купить за {product.price} руб.",
                            callback_data=f"buy_product_{product.id}"
                        )
                    ],
                    [
                        InlineKeyboardButton(
                            text="◀️ Назад к подкатегориям",
                            callback_data="back_to_subcategories"
                        )
                    ]
                ]
            )
        
        # Удаляем старое сообщение и отправляем новое
        await callback.message.delete()
        await callback.message.answer(
            text,
            reply_markup=keyboard,
            parse_mode="Markdown"
        )
    
    await callback.answer()
        
@router.callback_query(F.data.startswith("subcat_"))
async def show_products(callback: CallbackQuery, state: FSMContext):
    """Показать товары/работы/спортики выбранной подкатегории"""
    
    subcat = callback.data
    
    # Определяем категорию и подкатегорию
    subcategory_map = {
        # Марихуана
        "subcat_buds": ("weed", "buds"),
        "subcat_hash": ("weed", "hash"),
        "subcat_oil": ("weed", "oil"),
        "subcat_food": ("weed", "food"),
        # Работа
        "subcat_courier": ("job", "courier"),
        "subcat_transport": ("job", "transport"),
        "subcat_moderator": ("job", "moderator"),
        "subcat_sportik_job": ("job", "sportik"),
        # Спортики/Пробив
        "subcat_sport_pills": ("sports", "player"),  # Изменено с "pills" на "player"
        "subcat_search_person": ("sports", "search"),
    }
    
    if subcat not in subcategory_map:
        await callback.answer("Категория не найдена")
        return
    
    category, subcategory = subcategory_map[subcat]
    
    # Сохраняем информацию о текущей подкатегории
    await state.update_data(
        current_category=category,
        current_subcategory=subcategory
    )
    
    # Получаем товары/работы/спортики
    if subcategory == "all":
        # Для "Все категории" показываем все товары категории
        from data.products import ALL_PRODUCTS
        products = [p for p in ALL_PRODUCTS if p.category == category]
    else:
        products = get_products_by_subcategory(category, subcategory)
    
    if not products:
        from keyboards.inline import get_back_keyboard
        await callback.message.edit_text(
            "😔 В этой категории пока нет позиций.\n"
            "Скоро они появятся!",
            reply_markup=get_back_keyboard("catalog")
        )
        await callback.answer()
        return
    
    # Сохраняем товары для пользователя
    user_id = callback.from_user.id
    user_product_pages[user_id] = {
        "products": products,
        "page": 0,
        "category": category,
        "subcategory": subcategory
    }
    
    # Для категорий "job" и "sports" показываем список
    if category in ["job", "sports"]:
        await show_job_or_sports_list(callback, products, category, subcategory, page=0)
    else:
        # Для товаров показываем с фото
        await show_products_page(callback, user_id, page=0)
    
    await callback.answer()
    
    
    
@router.callback_query(F.data.startswith("products_page_"))
async def change_products_page(callback: CallbackQuery):
    """Смена страницы товаров"""
    user_id = callback.from_user.id
    page = int(callback.data.split("_")[2])
    
    if user_id in user_product_pages:
        category = user_product_pages[user_id]["category"]
        # Для категорий "job" и "sports" не поддерживаем пагинацию
        if category in ["job", "sports"]:
            await callback.answer("В этой категории одна страница")
            return
    
    await show_products_page(callback, user_id, page=page)
    await callback.answer()
    
    
@router.callback_query(F.data.startswith("product_"))
async def show_product_detail(callback: CallbackQuery):
    """Показать детальную информацию о товаре/работе/спортике"""
    product_id = int(callback.data.split("_")[1])
    product = get_product_by_id(product_id)
    
    if not product:
        await callback.answer("Позиция не найдена")
        return
    
    # Получаем данные из хранилища пользователя
    user_id = callback.from_user.id
    if user_id in user_product_pages:
        category = user_product_pages[user_id]["category"]
        subcategory = user_product_pages[user_id]["subcategory"]
    else:
        category = product.category
        subcategory = product.subcategory
    
    # Форматируем цену
    price_text = f"{product.price:,} {product.currency}".replace(",", " ")
    
    # Формируем описание
    description = f"""*{product.name}*\n\n{product.description}"""
    
    # Добавляем цену если не работа
    if category != "job":
        description += f"\n\n💰 *Цена:* {price_text}"
    
    # Для работ показываем только кнопку "Назад"
    if category == "job":
        from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="◀️ Назад к подкатегориям",
                        callback_data="back_to_subcategories"
                    )
                ]
            ]
        )
        
        # Удаляем старое сообщение и отправляем новое
        await callback.message.delete()
        await callback.message.answer(
            description,
            reply_markup=keyboard,
            parse_mode="Markdown"
        )
    elif category == "sports":
        # Для спортиков показываем кнопку покупки без фото
        from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text=f"💰 Купить за {product.price} руб.",
                        callback_data=f"buy_product_{product.id}"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="◀️ Назад к подкатегориям",
                        callback_data="back_to_subcategories"
                    )
                ]
            ]
        )
        
        await callback.message.delete()
        await callback.message.answer(
            description,
            reply_markup=keyboard,
            parse_mode="Markdown"
        )
    else:
        # Для товаров марихуаны показываем фото и кнопку покупки
        # Получаем фото товара
        product_photo = get_product_photo_file(product.id, category, subcategory)
        
        # Отправляем фото товара с описанием
        await callback.message.delete()
        
        await callback.message.answer_photo(
            photo=product_photo,
            caption=description,
            reply_markup=get_product_detail_keyboard(product, category, subcategory),
            parse_mode="Markdown"
        )
    
    await callback.answer()

@router.callback_query(F.data.startswith("buy_product_"))
async def process_buy_product(callback: CallbackQuery):
    """Обработка нажатия на кнопку покупки товара/спортика/пробива"""
    try:
        # Получаем ID товара из callback_data (формат: buy_product_1)
        product_id = int(callback.data.split("_")[2])
        product = get_product_by_id(product_id)
        
        if not product:
            await callback.answer("Товар не найден!")
            return
        
        # Проверяем категорию
        if product.category == "job":
            await callback.answer("Для работы нажмите кнопку 'Назад'")
            return
        
        # Создаем платежную ссылку
        payment_result = await crypto_pay.create_invoice(
            amount=product.price,
            currency="RUB"
        )
        
        if not payment_result["success"]:
            await callback.answer(f"Ошибка: {payment_result.get('error', 'Неизвестная ошибка')}")
            return
        
        # Создаем клавиатуру
        from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
        
        payment_keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="💳 Оплатить сейчас",
                        url=payment_result["pay_url"]
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="✅ Проверить оплату",
                        callback_data=f"check_payment_{payment_result['invoice_id']}"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="🔙 Назад к товару",
                        callback_data=f"product_{product_id}"
                    )
                ]
            ]
        )
        
        # Формируем текст для замены
        payment_text = (
            f"💳 *Оплата услуги*\n\n"  # Изменено с "товара" на "услуги"
            f"*Услуга:* {product.name}\n"
            f"*Цена:* {product.price} руб.\n\n"
            f"1. Нажмите кнопку '💳 Оплатить сейчас'\n"
            f"2. Оплатите счет\n"
            f"3. Вернитесь в бот и нажмите '✅ Проверить оплату'\n\n"
            f"Если не умете пользоваться криптой, есть СБП @Api312'\n\n"
            f"*После оплаты свяжитесь с оператором @Api3211*"  # Добавлена ссылка на оператора
        )
        
        # Проверяем, является ли сообщение фото или текстом
        if callback.message.photo:
            # Если сообщение содержит фото - меняем подпись и клавиатуру
            await callback.message.edit_caption(
                caption=payment_text,
                reply_markup=payment_keyboard,
                parse_mode="Markdown"
            )
        else:
            # Если сообщение текстовое - меняем текст и клавиатуру
            await callback.message.edit_text(
                payment_text,
                reply_markup=payment_keyboard,
                parse_mode="Markdown"
            )
        
        await callback.answer()
        
    except Exception as e:
        import logging
        logging.error(f"Ошибка при покупке товара: {e}")
        await callback.answer("Произошла ошибка. Попробуйте позже.")



                                        
@router.callback_query(F.data.startswith("product_"))
async def show_product_detail(callback: CallbackQuery):
    """Показать детальную информацию о товаре с фото"""
    product_id = int(callback.data.split("_")[1])
    product = get_product_by_id(product_id)
    
    if not product:
        await callback.answer("Товар не найден")
        return
    
    # Получаем данные из хранилища пользователя
    user_id = callback.from_user.id
    if user_id in user_product_pages:
        category = user_product_pages[user_id]["category"]
        subcategory = user_product_pages[user_id]["subcategory"]
    else:
        category = product.category
        subcategory = product.subcategory
    
    # Форматируем цену
    price_text = f"{product.price:,} {product.currency}".replace(",", " ")
    
    # Формируем описание
    description = f"""
{product.name}
━━━━━━━━━━━━━━━━━━━━
{product.description}

💰 Цена: {price_text}
📦 В наличии: {product.quantity} шт.

✅ Доступен для заказа
    """
    
    # Получаем фото товара
    product_photo = get_product_photo_file(product.id, category, subcategory)
    
    # Отправляем фото товара с описанием
    await callback.message.delete()
    
    await callback.message.answer_photo(
        photo=product_photo,
        caption=description,
        reply_markup=get_product_detail_keyboard(product, category, subcategory)
    )
    await callback.answer()

@router.callback_query(F.data.startswith("buy_product_"))
async def process_buy_product(callback: CallbackQuery):
    """Обработка нажатия на кнопку покупки товара"""
    try:
        # Получаем ID товара из callback_data (формат: buy_product_1)
        product_id = int(callback.data.split("_")[2])
        product = get_product_by_id(product_id)
        
        if not product:
            await callback.answer("Товар не найден!")
            return
        
        # Создаем платежную ссылку
        payment_result = await crypto_pay.create_invoice(
            amount=product.price,
            currency="RUB"
        )
        
        if not payment_result["success"]:
            await callback.answer(f"Ошибка: {payment_result.get('error', 'Неизвестная ошибка')}")
            return
        
        # Создаем клавиатуру
        from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
        
        payment_keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="💳 Оплатить сейчас",
                        url=payment_result["pay_url"]
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="✅ Проверить оплату",
                        callback_data=f"check_payment_{payment_result['invoice_id']}"
                    )
                ],

                [
                    InlineKeyboardButton(
                        text="🔙 Назад к товару",
                        callback_data=f"product_{product_id}"
                    )
                ]
            ]
        )
        
        # Формируем текст для замены
        payment_text = (
            f"💳 *Оплата товара*\n\n"
            f"*Товар:* {product.name}\n"
            f"*Цена:* {product.price} руб.\n\n"
            f"1. Нажмите кнопку '💳 Оплатить сейчас'\n"
            f"2. Оплатите счет\n"
            f"3. Вернитесь в бот и нажмите '✅ Проверить оплату'\n\n"
            f"Если не умете пользоваться криптой, есть СБП @Api312'\n\n"
            f"*После оплаты вы получите адрес.*"
        )
        
        # ВАЖНО: Проверяем, является ли сообщение фото или текстом
        if callback.message.photo:
            # Если сообщение содержит фото - меняем подпись и клавиатуру
            await callback.message.edit_caption(
                caption=payment_text,
                reply_markup=payment_keyboard,
                parse_mode="Markdown"
            )
        else:
            # Если сообщение текстовое - меняем текст и клавиатуру
            await callback.message.edit_text(
                payment_text,
                reply_markup=payment_keyboard,
                parse_mode="Markdown"
            )
        
        await callback.answer()
        
    except Exception as e:
        import logging
        logging.error(f"Ошибка при покупке товара: {e}")
        await callback.answer("Произошла ошибка. Попробуйте позже.")

@router.callback_query(F.data.startswith("check_payment_"))
async def check_payment_status(callback: CallbackQuery):
    """Проверка статуса платежа"""
    try:
        invoice_id = int(callback.data.split("_")[2])
        
        # Проверяем статус платежа
        payment_status = await crypto_pay.check_payment(invoice_id)
        
        if payment_status["paid"]:
            # Платеж успешен
            await callback.message.answer(
                "✅ *Оплата подтверждена!*\n\n"
                "📞 *Свяжитесь с оператором для получения услуги:*\n"  # Изменено с "адреса" на "услуги"
                "👤 @Api3211\n\n"  # Изменен контакт оператора
                "⏰ *Время работы:*\n"
                "Круглосуточно\n\n"
                "*После связи с оператором вы получите все детали.*",  # Измененный текст
                parse_mode="Markdown"
            )
        else:
            await callback.answer("Оплата еще не поступила. Если вы оплатили, подождите несколько минут.")
            
    except Exception as e:
        import logging
        logging.error(f"Ошибка при проверке платежа: {e}")
        await callback.answer("Ошибка проверки платежа")

@router.callback_query(F.data.startswith("back_to_products_"))
async def back_to_products(callback: CallbackQuery):
    """Возврат к списку товаров"""
    parts = callback.data.split("_")
    if len(parts) >= 5:
        category = parts[3]
        subcategory = parts[4]
        
        user_id = callback.from_user.id
        if user_id in user_product_pages:
            data = user_product_pages[user_id]
            page = data.get("page", 0)
            # Для категорий "job" и "sports" не используем show_products_page
            if category in ["job", "sports"]:
                products = data["products"]
                await show_job_or_sports_list(callback, products, category, subcategory, page)
            else:
                await show_products_page(callback, user_id, page=page)
    await callback.answer()
    
@router.callback_query(F.data == "back_to_subcategories")
async def back_to_subcategories(callback: CallbackQuery):
    """Возврат к подкатегориям - ОСОБЫЙ ОБРАБОТЧИК"""
    # Нужно определить, из какой категории пришли
    user_id = callback.from_user.id
    
    # Удаляем текущее сообщение (с фото)
    await callback.message.delete()
    
    # Отправляем новое сообщение с подкатегориями
    if user_id in user_product_pages:
        category = user_product_pages[user_id]["category"]
        
        if category == "weed":
            await callback.message.answer(
                "🌿 Марихуана\n\n"
                "Выберите подкатегорию:",
                reply_markup=get_weed_subcategories_keyboard()
            )
        elif category == "job":
            await callback.message.answer(
                "🔧 Работа\n\n"
                "Выберите подкатегорию:",
                reply_markup=get_job_subcategories_keyboard()
            )
        elif category == "sports":
            await callback.message.answer(
                "🥊 Спортики/пробив\n\n"
                "Выберите подкатегорию:",
                reply_markup=get_sports_subcategories_keyboard()
            )
        else:
            from keyboards.inline import get_catalog_keyboard
            await callback.message.answer(
                "🛍 Каталог товаров\n\n"
                "Выберите категорию:",
                reply_markup=get_catalog_keyboard()
            )
    else:
        from keyboards.inline import get_catalog_keyboard
        await callback.message.answer(
            "🛍 Каталог товаров\n\n"
            "Выберите категорию:",
            reply_markup=get_catalog_keyboard()
        )
    
    await callback.answer()
    