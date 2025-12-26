from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass
class User:
    id: int
    telegram_id: int
    city: str = None
    metro: str = None
    created_at: datetime = None
    updated_at: datetime = None

@dataclass
class UserSettings:
    id: int
    user_id: int
    city: str = None
    metro: str = None
    created_at: datetime = None

@dataclass
class Product:
    id: int
    name: str
    category: str
    subcategory: str
    price: float
    currency: str
    description: str
    quantity: int
    created_at: datetime = None

# НОВАЯ МОДЕЛЬ ДЛЯ ЗАКАЗОВ (минимальная)
@dataclass
class Order:
    id: int
    user_id: int
    product_id: int
    invoice_id: Optional[int] = None  # ID платежа в CryptoPay
    amount: float = 0.0
    status: str = "pending"  # pending, paid, cancelled
    payment_url: Optional[str] = None  # Ссылка для оплаты
    created_at: datetime = None
    updated_at: datetime = None