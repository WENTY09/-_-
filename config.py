"""
Configuration module for Delivery Bot
"""
import os
import logging

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Bot Configuration
TELEGRAM_BOT_TOKEN = "7991697168:AAF1GxpKVE1M1N-QSJ-eKiKm47g775jtPJ8"

# Admin Configuration
ADMIN_IDS = [
    "6999938953",  # Главный администратор
]

# Database Configuration
DATABASE_URL = "postgresql://neondb_owner:npg_Sv5uoEPq4Wxr@ep-odd-resonance-a4sl06ma.us-east-1.aws.neon.tech/neondb?sslmode=require"

# Session Configuration
SESSION_SECRET = "zE31T4akjO0gpeoW7cnCKgw2DPy5EyGXOEkAchU5YjoOs2RdQx4mMRwpaycIWMhiy/+fr6eBZVsLxPph8e+0cw=="

# PostgreSQL Configuration
PG_CONFIG = {
    "database": "neondb",
    "host": "ep-odd-resonance-a4sl06ma.us-east-1.aws.neon.tech",
    "port": "5432",
    "user": "neondb_owner",
    "password": "npg_Sv5uoEPq4Wxr"
}

# Shop Item Configuration
DEFAULT_SHOP_ITEMS = [
    {
        "id": "hyper_buff",
        "name": "Гипер Бафф",
        "description": "Повышает доход на 50%",
        "price": 2750,
        "duration_minutes": 40,
        "earning_multiplier": 0.5
    },
    {
        "id": "super_buff",
        "name": "Супер Бафф",
        "description": "Повышает доход на 15%",
        "price": 850,
        "duration_minutes": 30,
        "earning_multiplier": 0.15
    },
    {
        "id": "mega_buff",
        "name": "Мега Бафф",
        "description": "Повышает доход на 25%",
        "price": 1800,
        "duration_minutes": 30,
        "earning_multiplier": 0.25
    }
]

# Game Configuration
DELIVERY_COOLDOWN_MINUTES = 7

# Директории для файлов
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, 'data')
USER_DATA_FILE = os.path.join(DATA_DIR, 'user_data.json')
SHOP_DATA_FILE = os.path.join(DATA_DIR, 'shop_items.json')
STATS_DATA_FILE = os.path.join(DATA_DIR, 'stats.json')

# Создаем директорию для данных, если её нет
os.makedirs(DATA_DIR, exist_ok=True)

# Настройки Flask
FLASK_SECRET_KEY = SESSION_SECRET
SQLALCHEMY_TRACK_MODIFICATIONS = False
SQLALCHEMY_ENGINE_OPTIONS = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}
