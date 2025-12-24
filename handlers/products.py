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
    
    # Обновляем текущую страницу
    data["page"] = page
    
    # Определяем заголовок категории
    category_names = {
        "buds": "🌿 Шишки",
        "hash": "🍫 Гашиш",
        "oil": "💧 Масло/Вэйп",
        "food": "🍪 Cannafood",
    }
    
    category_name = category_names.get(subcategory, "Товары")
    
    # Получаем фото категории для конкретной страницы
    category_photo = get_category_photo_file(category, subcategory, page)
    
    # Формируем подпись
    total_pages = (len(products) + 3) // 4  # 4 товара на страницу
    caption = f"{category_name}\n\n"
    caption += f"Страница: {page + 1}/{total_pages}\n"
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

@router.callback_query(F.data.startswith("subcat_"))
async def show_products(callback: CallbackQuery, state: FSMContext):
    """Показать товары выбранной подкатегории с фото"""
    
    subcat = callback.data
    
    # Определяем категорию и подкатегорию
    subcategory_map = {
        # Марихуана
        "subcat_buds": ("weed", "buds"),
        "subcat_hash": ("weed", "hash"),
        "subcat_oil": ("weed", "oil"),
        "subcat_food": ("weed", "food"),
        "subcat_all_weed": ("weed", "all"),
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
    
    # Получаем товары
    if subcategory == "all":
        # Для "Все категории" показываем все товары категории
        from data.products import ALL_PRODUCTS
        products = [p for p in ALL_PRODUCTS if p.category == category]
    else:
        products = get_products_by_subcategory(category, subcategory)
    
    if not products:
        from keyboards.inline import get_back_keyboard
        await callback.message.edit_text(
            "😔 В этой категории пока нет товаров.\n"
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
    
    # Показываем первую страницу
    await show_products_page(callback, user_id, page=0)
    await callback.answer()

@router.callback_query(F.data.startswith("products_page_"))
async def change_products_page(callback: CallbackQuery):
    """Смена страницы товаров"""
    user_id = callback.from_user.id
    page = int(callback.data.split("_")[2])
    await show_products_page(callback, user_id, page=page)
    await callback.answer()

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