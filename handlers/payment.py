from aiogram import Router, F
from aiogram.types import CallbackQuery, Message, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
import asyncio

from data.products import get_product_by_id
from database.database import get_user_city, get_user_metro
from payment.cryptobot import CryptoBotPayment
from config import CRYPTOBOT_API_TOKEN, CRYPTOBOT_TEST_MODE, SHOP_NAME, COMMISSION_PERCENT, DELIVERY_COST, MIN_ORDER_AMOUNT
from keyboards.inline import get_back_keyboard
import logging
from config import SUPPORT_USERNAME

router = Router()

# Инициализируем платежную систему
cryptobot = CryptoBotPayment(CRYPTOBOT_API_TOKEN, CRYPTOBOT_TEST_MODE)

# Настройка логгера
logger = logging.getLogger(__name__)

# Состояния для оформления заказа
class OrderStates(StatesGroup):
    waiting_for_quantity = State()
    waiting_for_address = State()
    waiting_for_comment = State()
    waiting_for_payment = State()

# Хранилище для временных данных заказа
user_orders = {}

@router.callback_query(F.data.startswith("buy_"))
async def start_purchase(callback: CallbackQuery, state: FSMContext):
    """Начало оформления покупки"""
    product_id = int(callback.data.split("_")[1])
    product = get_product_by_id(product_id)
    
    if not product:
        await callback.answer("Товар не найден")
        return
    
    if product.quantity <= 0:
        await callback.answer("Товар временно отсутствует")
        return
    
    # Сохраняем информацию о товаре
    await state.update_data(
        product_id=product_id,
        product_name=product.name,
        product_price=product.price,
        max_quantity=product.quantity
    )
    
    # Создаем клавиатуру для выбора количества
    keyboard = InlineKeyboardMarkup(inline_keyboard=[])
    
    # Кнопки количества (от 1 до 5 или доступное количество)
    max_qty = min(5, product.quantity)
    row = []
    for i in range(1, max_qty + 1):
        row.append(InlineKeyboardButton(text=str(i), callback_data=f"qty_{i}"))
        if len(row) == 3:
            keyboard.inline_keyboard.append(row)
            row = []
    if row:
        keyboard.inline_keyboard.append(row)
    
    # Кнопка назад
    keyboard.inline_keyboard.append([
        InlineKeyboardButton(
            text="◀️ Назад к товару",
            callback_data=f"product_{product_id}"
        )
    ])
    
    await callback.message.edit_text(
        f"🛒 Покупка: {product.name}\n"
        f"💰 Цена за 1г/шт: {product.price} {product.currency}\n"
        f"📦 В наличии: {product.quantity} шт.\n\n"
        "Выберите количество:",
        reply_markup=keyboard
    )
    await callback.answer()

@router.callback_query(F.data.startswith("qty_"))
async def process_quantity(callback: CallbackQuery, state: FSMContext):
    """Обработка выбора количества"""
    quantity = int(callback.data.split("_")[1])
    
    # Получаем данные из состояния
    data = await state.get_data()
    product_price = data["product_price"]
    product_name = data["product_name"]
    
    # Рассчитываем сумму
    total = product_price * quantity
    
    # Сохраняем количество
    await state.update_data(quantity=quantity, total_amount=total)
    
    # Запрашиваем адрес доставки
    await callback.message.edit_text(
        f"🛒 Покупка: {product_name}\n"
        f"📦 Количество: {quantity} шт.\n"
        f"💰 Общая сумма: {total} RUB\n\n"
        "📍 Укажите адрес доставки (улица, дом, квартира):",
        reply_markup=get_back_keyboard("product")
    )
    
    await state.set_state(OrderStates.waiting_for_address)
    await callback.answer()

@router.message(OrderStates.waiting_for_address)
async def process_address(message: Message, state: FSMContext):
    """Обработка адреса доставки"""
    address = message.text.strip()
    
    if len(address) < 5:
        await message.answer("❌ Адрес слишком короткий. Укажите полный адрес:")
        return
    
    # Получаем город и метро пользователя
    city = await get_user_city(message.from_user.id)
    metro = await get_user_metro(message.from_user.id)
    
    # Сохраняем адрес
    await state.update_data(
        address=address,
        city=city,
        metro=metro,
        user_id=message.from_user.id,
        username=message.from_user.username or f"id{message.from_user.id}"
    )
    
    # Запрашиваем комментарий
    await message.answer(
        "💬 Добавьте комментарий к заказу (необязательно):\n"
        "Например: время доставки, особенности и т.д.\n\n"
        "Или напишите 'нет' если комментарий не нужен.",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[[
            InlineKeyboardButton(text="🔄 Без комментария", callback_data="no_comment")
        ]])
    )
    
    await state.set_state(OrderStates.waiting_for_comment)

@router.callback_query(F.data == "no_comment", OrderStates.waiting_for_comment)
async def skip_comment(callback: CallbackQuery, state: FSMContext):
    """Пропустить комментарий"""
    await state.update_data(comment="Без комментария")
    await process_order_summary(callback, state)

@router.message(OrderStates.waiting_for_comment)
async def process_comment(message: Message, state: FSMContext):
    """Обработка комментария к заказу"""
    comment = message.text.strip()
    
    if comment.lower() in ['нет', 'no', 'без', 'skip']:
        comment = "Без комментария"
    
    await state.update_data(comment=comment)
    await process_order_summary(message, state)

async def process_order_summary(update, state: FSMContext):
    """Показать сводку заказа и перейти к оплате"""
    data = await state.get_data()
    
    # Рассчитываем итоговую сумму с доставкой
    total_with_delivery = data["total_amount"] + DELIVERY_COST
    
    # Формируем сводку
    summary_text = f"""
📋 Сводка заказа:
━━━━━━━━━━━━━━━━━━━━
🛒 Товар: {data['product_name']}
📦 Количество: {data['quantity']} шт.
💰 Сумма товаров: {data['total_amount']} RUB
🚚 Доставка: {DELIVERY_COST} RUB
━━━━━━━━━━━━━━━━━━━━
💎 ИТОГО: {total_with_delivery} RUB
━━━━━━━━━━━━━━━━━━━━
📍 Адрес: {data['address']}
🏙️ Город: {data['city'] or 'Не указан'}
🚇 Метро: {data['metro'] or 'Не указано'}
💬 Комментарий: {data.get('comment', 'Без комментария')}
━━━━━━━━━━━━━━━━━━━━
"""
    
    # Клавиатура для подтверждения
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="✅ Подтвердить и оплатить",
                callback_data="confirm_order"
            )
        ],
        [
            InlineKeyboardButton(
                text="◀️ Назад",
                callback_data="back_to_quantity"
            )
        ]
    ])
    
    if hasattr(update, 'message'):
        await update.message.answer(summary_text, reply_markup=keyboard)
    else:
        await update.edit_text(summary_text, reply_markup=keyboard)
    
    await state.set_state(OrderStates.waiting_for_payment)

@router.callback_query(F.data == "back_to_quantity")
async def back_to_quantity(callback: CallbackQuery, state: FSMContext):
    """Вернуться к выбору количества"""
    data = await state.get_data()
    product_id = data["product_id"]
    
    # Возвращаем к началу покупки
    await start_purchase(callback, state)
    await callback.answer()

@router.callback_query(F.data == "confirm_order")
async def create_payment(callback: CallbackQuery, state: FSMContext):
    """Создание платежа"""
    data = await state.get_data()
    
    # Проверяем минимальную сумму
    total_with_delivery = data["total_amount"] + DELIVERY_COST
    if total_with_delivery < MIN_ORDER_AMOUNT:
        await callback.message.edit_text(
            f"❌ Минимальная сумма заказа: {MIN_ORDER_AMOUNT} RUB\n"
            f"Ваша сумма: {total_with_delivery} RUB\n\n"
            "Добавьте больше товаров или выберите другой товар.",
            reply_markup=get_back_keyboard("product")
        )
        await callback.answer()
        return
    
    # Создаем описание заказа
    order_description = f"""
🛒 Заказ #{callback.id % 10000}
━━━━━━━━━━━━━━━━━━━━
Товар: {data['product_name']}
Количество: {data['quantity']} шт.
Адрес: {data['address']}
Город: {data['city']}
Метро: {data['metro']}
━━━━━━━━━━━━━━━━━━━━
Сумма: {total_with_delivery} RUB
"""
    
    try:
        # Создаем счет в CryptoBot
        invoice = cryptobot.create_invoice(
            amount=total_with_delivery,
            currency="RUB",
            asset="USDT",  # Можно изменить на BTC, ETH, TON
            description=f"Оплата заказа #{callback.id % 10000}",
            hidden_message="✅ Заказ оплачен! С вами свяжется оператор.",
            paid_btn_name="callback",
            paid_btn_url=f"https://t.me/{SHOP_NAME}",
            payload=str(callback.from_user.id),
            expires_in=3600  # 1 час
        )
        
        # Сохраняем информацию о заказе
        order_id = invoice.get("invoice_id")
        user_orders[order_id] = {
            "user_id": callback.from_user.id,
            "product_id": data["product_id"],
            "quantity": data["quantity"],
            "total_amount": total_with_delivery,
            "address": data["address"],
            "city": data["city"],
            "metro": data["metro"],
            "comment": data.get("comment", ""),
            "status": "pending",
            "invoice_url": invoice.get("pay_url"),
            "created_at": callback.date
        }
        
        # Отправляем ссылку на оплату
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="💎 Оплатить через CryptoBot",
                    url=invoice.get("pay_url")
                )
            ],
            [
                InlineKeyboardButton(
                    text="🔄 Проверить оплату",
                    callback_data=f"check_payment_{order_id}"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🏠 В главное меню",
                    callback_data="back_to_main_menu"
                )
            ]
        ])
        
        await callback.message.edit_text(
            f"💎 Оплата заказа #{order_id}\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"Сумма к оплате: {total_with_delivery} RUB\n"
            f"Криптовалюта: USDT\n\n"
            f"📋 Детали заказа:\n"
            f"• Товар: {data['product_name']}\n"
            f"• Количество: {data['quantity']} шт.\n"
            f"• Адрес: {data['address']}\n\n"
            f"⏰ Счет действителен 1 час\n"
            f"💡 После оплаты нажмите 'Проверить оплату'",
            reply_markup=keyboard
        )
        
        # Запускаем проверку оплаты в фоне
        asyncio.create_task(check_payment_periodically(order_id, callback.from_user.id))
        
    except Exception as e:
        logger.error(f"Payment creation error: {e}")
        await callback.message.edit_text(
            "❌ Ошибка при создании платежа. Попробуйте позже.",
            reply_markup=get_back_keyboard("main_menu")
        )
    
    await callback.answer()

@router.callback_query(F.data.startswith("check_payment_"))
async def check_payment(callback: CallbackQuery):
    """Проверка оплаты"""
    order_id = int(callback.data.split("_")[2])
    
    if order_id not in user_orders:
        await callback.answer("Заказ не найден")
        return
    
    order = user_orders[order_id]
    
    try:
        is_paid = cryptobot.is_invoice_paid(order_id)
        
        if is_paid:
            # Обновляем статус заказа
            order["status"] = "paid"
            order["paid_at"] = callback.date
            
            # Отправляем подтверждение
            await callback.message.edit_text(
                f"✅ Заказ #{order_id} оплачен!\n"
                f"━━━━━━━━━━━━━━━━━━━━\n"
                f"💰 Сумма: {order['total_amount']} RUB\n"
                f"📦 Товар: {order['product_id']}\n"
                f"📍 Адрес: {order['address']}\n\n"
                f"📞 С вами свяжется оператор для уточнения деталей доставки.\n"
                f"⏰ Обычно в течение 30 минут.\n\n"
                f"💬 Для связи: {SUPPORT_USERNAME}",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[[
                    InlineKeyboardButton(text="🏠 В главное меню", callback_data="back_to_main_menu")
                ]])
            )
            
            # Здесь можно добавить сохранение заказа в БД
            # и отправку уведомления администратору
            
        else:
            await callback.answer("❌ Оплата еще не поступила")
            
    except Exception as e:
        logger.error(f"Payment check error: {e}")
        await callback.answer("⚠️ Ошибка при проверке оплаты")

async def check_payment_periodically(order_id: int, user_id: int):
    """Периодическая проверка оплаты"""
    for _ in range(60):  # Проверяем 60 раз (1 час)
        await asyncio.sleep(60)  # Каждую минуту
        
        if order_id not in user_orders:
            break
        
        try:
            if cryptobot.is_invoice_paid(order_id):
                # Отправляем уведомление пользователю
                # Можно добавить отправку сообщения
                user_orders[order_id]["status"] = "paid"
                break
        except Exception as e:
            logger.error(f"Periodic check error: {e}")
    
    # Очищаем старые заказы
    if order_id in user_orders and user_orders[order_id]["status"] == "pending":
        del user_orders[order_id]

@router.callback_query(F.data == "back_to_main_menu")
async def back_to_main_from_payment(callback: CallbackQuery):
    """Возврат в главное меню из оплаты"""
    from handlers.main_menu import start_main_menu
    await start_main_menu(callback)
    await callback.answer()