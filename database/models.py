from dataclasses import dataclass
from datetime import datetime

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

# Модель товара оставляем на будущее
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