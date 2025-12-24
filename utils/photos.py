import os
from aiogram.types import FSInputFile, InputMediaPhoto
from config import DEFAULT_CATEGORY_PHOTO, DEFAULT_PRODUCT_PHOTO, CATEGORY_PHOTOS_DIR, PRODUCT_PHOTOS_DIR

def get_category_photo_path(category: str, subcategory: str, page: int = 0) -> str:
    """
    Получить путь к фото категории для конкретной страницы
    
    Ищет файлы в порядке:
    1. category_subcategory_page.jpg (например: weed_buds_1.jpg)
    2. category_subcategory.jpg (например: weed_buds.jpg)
    3. default.jpg
    """
    # Пробуем найти фото с номером страницы
    filename_with_page = f"{category}_{subcategory}_{page + 1}.jpg"
    path_with_page = os.path.join(CATEGORY_PHOTOS_DIR, filename_with_page)
    
    if os.path.exists(path_with_page):
        return path_with_page
    
    # Пробуем найти общее фото категории
    filename = f"{category}_{subcategory}.jpg"
    path = os.path.join(CATEGORY_PHOTOS_DIR, filename)
    
    if os.path.exists(path):
        return path
    
    # Возвращаем дефолтное фото
    return DEFAULT_CATEGORY_PHOTO

def get_product_photo_path(product_id: int, category: str, subcategory: str) -> str:
    """Получить путь к фото товара"""
    # Пробуем несколько вариантов имен файлов
    possible_filenames = [
        f"{category}_{subcategory}_{product_id}.jpg",  # weed_buds_1.jpg
        f"{category}_{product_id}.jpg",  # weed_1.jpg
        f"product_{product_id}.jpg",  # product_1.jpg
        f"{product_id}.jpg",  # 1.jpg
    ]
    
    for filename in possible_filenames:
        path = os.path.join(PRODUCT_PHOTOS_DIR, filename)
        if os.path.exists(path):
            return path
    
    # Возвращаем дефолтное фото
    return DEFAULT_PRODUCT_PHOTO

def get_category_photo_file(category: str, subcategory: str, page: int = 0) -> FSInputFile:
    """Получить фото категории как FSInputFile"""
    path = get_category_photo_path(category, subcategory, page)
    return FSInputFile(path)

def get_product_photo_file(product_id: int, category: str, subcategory: str) -> FSInputFile:
    """Получить фото товара как FSInputFile"""
    path = get_product_photo_path(product_id, category, subcategory)
    return FSInputFile(path)

def get_photo_media(path: str, caption: str = "") -> InputMediaPhoto:
    """Создать InputMediaPhoto из пути"""
    return InputMediaPhoto(media=FSInputFile(path), caption=caption)