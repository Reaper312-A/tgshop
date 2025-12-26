import logging
from aiocryptopay import AioCryptoPay, Networks
from config import CRYPTO_PAY_TOKEN

logger = logging.getLogger(__name__)

class CryptoPayment:
    def __init__(self):
        # Используем MAIN_NET
        self.crypto = AioCryptoPay(
            token=CRYPTO_PAY_TOKEN,
            network=Networks.MAIN_NET
        )
        logger.info("✅ Инициализирован CryptoPay (MAIN_NET)")
    
    async def create_invoice(self, amount: float, currency: str = "RUB"):
        """Создать платежную ссылку"""
        try:
            # Проверяем подключение
            me = await self.crypto.get_me()
            logger.info(f"✅ Подключение успешно. Магазин: {me.name}")
            
            # Для рублевых цен конвертируем в USDT
            if currency == "RUB":
                # Примерный курс: 1 USDT = 90 RUB
                usdt_amount = max(1.0, round(amount / 90, 2))
                asset = "USDT"
            else:
                asset = currency.upper()
                usdt_amount = amount
            
            logger.info(f"🔄 Создаю инвойс: {usdt_amount} {asset} (оригинал: {amount} {currency})")
            
            # Создаем инвойс
            invoice = await self.crypto.create_invoice(
                asset=asset,
                amount=usdt_amount
            )
            
            # Проверяем доступные атрибуты
            logger.info(f"✅ Создан инвойс #{invoice.invoice_id} на сумму {usdt_amount} {asset}")
            
            # Пробуем разные возможные атрибуты для ссылки
            pay_url = None
            
            # Попробуем разные возможные названия атрибутов
            possible_url_attrs = [
                'pay_url', 'url', 'bot_url', 'invoice_url', 
                'payment_url', 'link', 'bot_invoice_url'
            ]
            
            for attr in possible_url_attrs:
                if hasattr(invoice, attr):
                    pay_url = getattr(invoice, attr)
                    logger.info(f"🔗 Найдена ссылка в атрибуте '{attr}': {pay_url}")
                    break
            
            # Если не нашли, пробуем получить через bot_username
            if not pay_url and hasattr(invoice, 'bot_username'):
                bot_username = invoice.bot_username
                pay_url = f"https://t.me/{bot_username.lstrip('@')}?start=pay_{invoice.invoice_id}"
                logger.info(f"🔗 Сгенерирована ссылка через bot_username: {pay_url}")
            
            # Если все еще нет ссылки, используем fallback
            if not pay_url:
                pay_url = f"https://t.me/CryptoBot?start=pay_{invoice.invoice_id}"
                logger.warning(f"⚠️ Ссылка не найдена, использую fallback: {pay_url}")
            
            return {
                "success": True,
                "pay_url": pay_url,
                "invoice_id": invoice.invoice_id,
                "amount": amount,
                "amount_crypto": usdt_amount,
                "currency": asset
            }
                
        except Exception as e:
            logger.error(f"❌ Ошибка при создании инвойса: {e}", exc_info=True)
            return {"success": False, "error": str(e)}
    
    async def check_payment(self, invoice_id: int):
        """Проверить статус платежа"""
        try:
            invoices = await self.crypto.get_invoices(invoice_ids=[invoice_id])
            if invoices:
                invoice = invoices[0]
                logger.info(f"📊 Статус инвойса #{invoice_id}: {invoice.status}")
                return {
                    "paid": invoice.status == "paid",
                    "status": invoice.status,
                    "amount": invoice.amount,
                    "currency": invoice.asset,
                    "expired": invoice.status == "expired"
                }
            logger.warning(f"⚠️ Инвойс #{invoice_id} не найден")
            return {"paid": False, "status": "not_found"}
        except Exception as e:
            logger.error(f"❌ Ошибка при проверке платежа: {e}")
            return {"paid": False, "status": "error"}
    
    async def close(self):
        """Закрытие соединения"""
        await self.crypto.close()