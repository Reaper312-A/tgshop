import logging
import aiohttp
import json
from config import CRYPTO_PAY_TOKEN

logger = logging.getLogger(__name__)

class CryptoPaymentFixed:
    def __init__(self):
        self.token = CRYPTO_PAY_TOKEN
        self.base_url = "https://api.crystalpay.io/v2"
        logger.info("✅ Инициализирован CryptoPaymentFixed")
    
    async def create_invoice(self, amount: float, currency: str = "RUB"):
        """Создать платежную ссылку через прямое API"""
        try:
            # Разбираем токен
            if ":" not in self.token:
                return {"success": False, "error": "Неверный формат токена"}
            
            auth_login, auth_secret = self.token.split(":", 1)
            
            # Конвертируем рубли в USDT
            if currency == "RUB":
                usdt_amount = max(1.0, round(amount / 90, 2))
                asset = "usdt"
            else:
                asset = currency.lower()
                usdt_amount = amount
            
            logger.info(f"🔄 Создаю инвойс: {usdt_amount} {asset} (оригинал: {amount} {currency})")
            
            # Данные для запроса
            data = {
                "auth_login": auth_login,
                "auth_secret": auth_secret,
                "amount": usdt_amount,
                "type": "purchase",
                "description": f"Оплата товара - {usdt_amount} {asset.upper()}",
                "currency": asset,
                "lifetime": 1440,  # 24 часа в минутах
                "redirect_url": "https://t.me/your_bot"
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/invoice/create/",
                    json=data,
                    headers={"Content-Type": "application/json"}
                ) as response:
                    result = await response.json()
                    
                    if result.get("error"):
                        logger.error(f"❌ API ошибка: {result}")
                        return {"success": False, "error": result.get("error")}
                    
                    if result.get("id"):
                        logger.info(f"✅ Создан инвойс #{result['id']}")
                        logger.info(f"🔗 Ссылка: {result.get('url')}")
                        
                        return {
                            "success": True,
                            "pay_url": result.get("url"),
                            "invoice_id": result.get("id"),
                            "amount": amount,
                            "amount_crypto": usdt_amount,
                            "currency": asset.upper()
                        }
            
            return {"success": False, "error": "Неизвестная ошибка API"}
                
        except Exception as e:
            logger.error(f"❌ Ошибка при создании инвойса: {e}", exc_info=True)
            return {"success": False, "error": str(e)}
    
    async def check_payment(self, invoice_id: int):
        """Проверить статус платежа"""
        try:
            if ":" not in self.token:
                return {"paid": False, "status": "error"}
            
            auth_login, auth_secret = self.token.split(":", 1)
            
            data = {
                "auth_login": auth_login,
                "auth_secret": auth_secret,
                "id": invoice_id
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/invoice/info/",
                    json=data,
                    headers={"Content-Type": "application/json"}
                ) as response:
                    result = await response.json()
                    
                    if result.get("error"):
                        logger.error(f"❌ API ошибка проверки: {result}")
                        return {"paid": False, "status": "error"}
                    
                    status = result.get("state", "active")
                    paid = status == "payed"  # Обратите внимание на опечатку в API: "payed"
                    
                    logger.info(f"📊 Статус инвойса #{invoice_id}: {status}")
                    
                    return {
                        "paid": paid,
                        "status": status,
                        "amount": result.get("amount"),
                        "currency": result.get("currency", "USDT").upper(),
                        "expired": status == "expired"
                    }
                    
        except Exception as e:
            logger.error(f"❌ Ошибка при проверке платежа: {e}")
            return {"paid": False, "status": "error"}
    
    async def close(self):
        """Закрытие соединения"""
        logger.info("Платежная система закрыта")