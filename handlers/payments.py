from aiogram import Router, types
from aiogram.types import CallbackQuery
import logging

from utils.payments_fixed import CryptoPaymentFixed
from database.database import create_order, update_order_status, get_order_by_invoice
from data.products import get_product_by_id

router = Router()
logger = logging.getLogger(__name__)

crypto_pay = CryptoPaymentFixed()


# ===================== УНИВЕРСАЛЬНАЯ КЛАВИАТУРА ОПЛАТЫ =====================
def build_payment_keyboard(pay_url: str, invoice_id: int, product_id: int) -> types.InlineKeyboardMarkup:
    return types.InlineKeyboardMarkup(
        inline_keyboard=[
            [
                types.InlineKeyboardButton(
                    text="💳 Оплатить сейчас",
                    url=pay_url
                )
            ],
            [
                types.InlineKeyboardButton(
                    text="✅ Проверить оплату",
                    callback_data=f"check_payment_{invoice_id}"
                )
            ],
            [
                types.InlineKeyboardButton(
                    text="❓ Инструкция",
                    callback_data="payment_instructions"
                )
            ],
            [
                types.InlineKeyboardButton(
                    text="🔙 Назад к товару",
                    callback_data=f"product_{product_id}"
                )
            ]
        ]
    )


# ===================== ПОКУПКА ТОВАРА =====================
@router.callback_query(lambda c: c.data.startswith("buy_product_"))
async def process_buy_product(callback: CallbackQuery):
    logger.info(f"🚀 buy_product | {callback.data}")

    try:
        product_id = int(callback.data.split("_")[2])
        product = get_product_by_id(product_id)

        if not product:
            await callback.answer("❌ Товар не найден", show_alert=True)
            return

        payment_result = await crypto_pay.create_invoice(
            amount=product.price,
            currency="RUB"
        )

        if not payment_result["success"]:
            await callback.answer("❌ Ошибка создания платежа", show_alert=True)
            return

        order_id = await create_order(
            user_id=callback.from_user.id,
            product_id=product_id,
            amount=product.price,
            invoice_id=payment_result["invoice_id"],
            payment_url=payment_result["pay_url"]
        )

        menu_text = (
            "<b>💳 Оплата товара</b>\n\n"
            f"<b>{product.name}</b>\n"
            f"Цена: {payment_result['amount_crypto']} USDT\n"
            f"ID заказа: #{order_id}\n\n"
            "После оплаты вы получите адрес."
        )

        keyboard = build_payment_keyboard(
            pay_url=payment_result["pay_url"],
            invoice_id=payment_result["invoice_id"],
            product_id=product_id
        )

        # Удаляем старое сообщение и отправляем новое
        try:
            await callback.message.delete()
        except:
            pass  # если удаление не удалось — продолжаем

        await callback.message.answer(
            menu_text,
            reply_markup=keyboard,
            parse_mode="HTML"
        )
        await callback.answer()

    except Exception as e:
        logger.exception(e)
        await callback.answer("⚠️ Ошибка. Попробуйте позже", show_alert=True)


# ===================== ПРОВЕРКА ПЛАТЕЖА =====================
@router.callback_query(lambda c: c.data.startswith("check_payment_"))
async def check_payment_status(callback: CallbackQuery):
    try:
        invoice_id = int(callback.data.split("_")[2])
        payment_status = await crypto_pay.check_payment(invoice_id)

        if payment_status.get("paid"):
            await update_order_status(invoice_id, "paid")
            order = await get_order_by_invoice(invoice_id)
            product = get_product_by_id(order["product_id"]) if order else None

            text = (
                "<b>✅ ОПЛАТА ПОДТВЕРЖДЕНА</b>\n\n"
                f"Товар: {product.name if product else '—'}\n"
                f"Сумма: {order['amount']} RUB\n"
                f"Оплачено: {payment_status.get('amount_crypto')} USDT\n"
                f"ID заказа: #{order['id']}\n\n"
                "<b>📍 Адрес самовывоза:</b>\n"
                "г. Москва, ул. Примерная, д. 10\n"
                "Работаем 24/7"
            )

            await callback.message.answer(text, parse_mode="HTML")
            await callback.answer("✅ Оплата подтверждена")

        elif payment_status.get("expired"):
            await callback.answer("⏰ Счет истёк", show_alert=True)

        else:
            await callback.answer("⏳ Платеж не найден", show_alert=False)

    except Exception as e:
        logger.exception(e)
        await callback.answer("⚠️ Ошибка проверки платежа", show_alert=True)


# ===================== ИНСТРУКЦИЯ =====================
@router.callback_query(lambda c: c.data == "payment_instructions")
async def show_payment_instructions(callback: CallbackQuery):
    text = (
        "<b>💡 Инструкция по оплате</b>\n\n"
        "1️⃣ Нажмите «💳 Оплатить сейчас»\n"
        "2️⃣ Оплатите USDT через CryptoBot\n"
        "3️⃣ Вернитесь и нажмите «✅ Проверить оплату»\n\n"
        "<b>⚠️ Важно:</b>\n"
        "• Только USDT\n"
        "• Сеть TRC20\n"
        "• Время зачисления: 1–10 минут\n"
        "• Счет действует 60 минут"
    )

    await callback.message.answer(text, parse_mode="HTML")
    await callback.answer()


# ===================== НАЗАД К ТОВАРУ =====================
@router.callback_query(lambda c: c.data.startswith("product_"))
async def back_to_product(callback: CallbackQuery):
    try:
        product_id = int(callback.data.split("_")[1])
        product = get_product_by_id(product_id)

        if not product:
            await callback.answer("❌ Товар не найден", show_alert=True)
            return

        text = (
            f"<b>📦 {product.name}</b>\n\n"
            f"{product.description}\n\n"
            f"Цена: {product.price} RUB\n\n"
            "Нажмите кнопку ниже для покупки 👇"
        )

        keyboard = types.InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    types.InlineKeyboardButton(
                        text="🛒 Купить",
                        callback_data=f"buy_product_{product_id}"
                    )
                ]
            ]
        )

        # Удаляем старое сообщение, чтобы чат не засорялся
        try:
            await callback.message.delete()
        except:
            pass

        await callback.message.answer(
            text,
            reply_markup=keyboard,
            parse_mode="HTML"
        )
        await callback.answer()

    except Exception as e:
        logger.exception(e)
        await callback.answer("⚠️ Ошибка", show_alert=True)