import requests
import json
import logging
from typing import Dict, Optional, List, Any
from datetime import datetime

logger = logging.getLogger(__name__)

class CryptoBotPayment:
    def __init__(self, api_token: str, test_mode: bool = False):
        """
        Инициализация CryptoBot платежной системы
        
        :param api_token: Токен API CryptoBot (формат: 123456:ABC123...)
        :param test_mode: Режим тестирования (True для тестов)
        """
        self.api_token = api_token
        self.test_mode = test_mode
        
        # Базовый URL API
        if test_mode:
            self.base_url = "https://testnet-pay.crypt.bot/api"
        else:
            self.base_url = "https://pay.crypt.bot/api"
        
        # Заголовки для запросов
        self.headers = {
            "Crypto-Pay-API-Token": self.api_token,
            "Content-Type": "application/json"
        }
        
        # Сессия для запросов
        self.session = requests.Session()
        self.session.headers.update(self.headers)
    
    def _make_request(self, method: str, endpoint: str, params: dict = None, data: dict = None) -> Dict:
        """
        Выполнить запрос к API CryptoBot
        
        :param method: HTTP метод (GET, POST)
        :param endpoint: Конечная точка API
        :param params: Параметры для GET запроса
        :param data: Данные для POST запроса
        :return: Ответ от API
        """
        url = f"{self.base_url}{endpoint}"
        
        try:
            logger.debug(f"Making {method} request to {url}")
            logger.debug(f"Params: {params}")
            logger.debug(f"Data: {data}")
            
            if method.upper() == "GET":
                response = self.session.get(url, params=params, timeout=30)
            else:
                response = self.session.post(url, json=data, timeout=30)
            
            logger.debug(f"Response status: {response.status_code}")
            logger.debug(f"Response body: {response.text[:500]}...")
            
            response.raise_for_status()
            result = response.json()
            
            if not result.get("ok"):
                error_msg = result.get("error", {}).get("name", "Unknown error")
                logger.error(f"CryptoBot API error: {error_msg}")
                raise Exception(f"CryptoBot API error: {error_msg}")
            
            return result.get("result", {})
            
        except requests.exceptions.Timeout:
            logger.error("Request timeout")
            raise Exception("Таймаут подключения к CryptoBot")
        except requests.exceptions.RequestException as e:
            logger.error(f"Request error: {e}")
            raise Exception(f"Ошибка подключения к CryptoBot: {e}")
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error: {e}")
            raise Exception(f"Ошибка обработки ответа от CryptoBot: {e}")
    
    def get_me(self) -> Dict:
        """Получить информацию о боте"""
        return self._make_request("GET", "/getMe")
    
    def create_invoice(
        self,
        amount: float,
        currency: str = "RUB",
        asset: str = "USDT",
        description: str = "Оплата товара",
        hidden_message: str = "Спасибо за покупку!",
        paid_btn_name: str = "callback",
        paid_btn_url: str = "",
        payload: str = None,
        allow_comments: bool = True,
        allow_anonymous: bool = True,
        expires_in: int = 3600
    ) -> Dict:
        """
        Создать счет на оплату
        
        :param amount: Сумма в валюте
        :param currency: Валюта суммы (RUB, USD, EUR и т.д.)
        :param asset: Криптовалюта для оплаты (USDT, BTC, ETH, TON и т.д.)
        :param description: Описание счета
        :param hidden_message: Сообщение после оплаты
        :param paid_btn_name: Тип кнопки после оплаты
        :param paid_btn_url: URL для кнопки после оплаты
        :param payload: Полезная нагрузка для callback
        :param allow_comments: Разрешить комментарии
        :param allow_anonymous: Разрешить анонимные платежи
        :param expires_in: Время жизни счета в секундах
        :return: Информация о счете
        """
        data = {
            "asset": asset,
            "amount": str(amount),
            "description": description[:1024],
            "hidden_message": hidden_message[:255],
            "paid_btn_name": paid_btn_name,
            "paid_btn_url": paid_btn_url,
            "allow_comments": str(allow_comments).lower(),
            "allow_anonymous": str(allow_anonymous).lower(),
            "expires_in": expires_in
        }
        
        if payload:
            data["payload"] = payload[:2048]
        
        if currency.upper() != "RUB":
            data["fiat"] = currency.upper()
            # Для фиатных валют нужно использовать метод createCheckout
            # Но для простоты пока используем крипто
        
        logger.info(f"Creating invoice: {data}")
        return self._make_request("POST", "/createInvoice", data=data)
    
    def get_invoices(
        self,
        asset: str = None,
        invoice_ids: str = None,
        status: str = None,
        offset: int = 0,
        count: int = 100
    ) -> Dict:
        """
        Получить список счетов
        
        :param asset: Фильтр по криптовалюте
        :param invoice_ids: ID счетов через запятую
        :param status: Статус (active, paid, expired)
        :param offset: Смещение
        :param count: Количество
        :return: Список счетов
        """
        params = {
            "offset": offset,
            "count": count
        }
        
        if asset:
            params["asset"] = asset
        if invoice_ids:
            params["invoice_ids"] = invoice_ids
        if status:
            params["status"] = status
        
        return self._make_request("GET", "/getInvoices", params=params)
    
    def get_balance(self) -> List[Dict]:
        """Получить баланс"""
        try:
            result = self._make_request("GET", "/getBalance")
            # Проверяем формат ответа
            if isinstance(result, list):
                return result
            elif isinstance(result, dict) and 'assets' in result:
                return result['assets']
            else:
                logger.warning(f"Unexpected balance format: {result}")
                return []
        except Exception as e:
            logger.error(f"Error getting balance: {e}")
            return []
    
    def get_exchange_rates(self) -> List[Dict]:
        """Получить курсы обмена"""
        try:
            result = self._make_request("GET", "/getExchangeRates")
            return result if isinstance(result, list) else []
        except Exception as e:
            logger.error(f"Error getting exchange rates: {e}")
            return []
    
    def get_currencies(self) -> List[Dict]:
        """Получить список доступных валют"""
        try:
            result = self._make_request("GET", "/getCurrencies")
            return result if isinstance(result, list) else []
        except Exception as e:
            logger.error(f"Error getting currencies: {e}")
            return []
    
    def check_invoice_status(self, invoice_id: int) -> Optional[str]:
        """
        Проверить статус счета
        
        :param invoice_id: ID счета
        :return: Статус (active, paid, expired) или None
        """
        try:
            invoices = self.get_invoices(invoice_ids=str(invoice_id))
            
            # Проверяем разные форматы ответа
            if isinstance(invoices, dict) and 'items' in invoices:
                items = invoices['items']
            elif isinstance(invoices, list):
                items = invoices
            else:
                items = []
            
            if items:
                invoice = items[0] if isinstance(items, list) else items
                return invoice.get('status')
                
        except Exception as e:
            logger.error(f"Error checking invoice status: {e}")
        
        return None
    
    def is_invoice_paid(self, invoice_id: int) -> bool:
        """
        Проверить, оплачен ли счет
        
        :param invoice_id: ID счета
        :return: True если оплачен
        """
        status = self.check_invoice_status(invoice_id)
        return status == "paid"
    
    def get_supported_assets(self) -> List[str]:
        """Получить список поддерживаемых криптоактивов"""
        try:
            currencies = self.get_currencies()
            return [c.get('code') for c in currencies if c.get('is_blockchain')]
        except Exception as e:
            logger.error(f"Error getting supported assets: {e}")
            return ["USDT", "BTC", "ETH", "TON", "BNB"]