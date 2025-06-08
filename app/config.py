import os
from dotenv import load_dotenv

# Загрузка переменные окружения из файла .env
load_dotenv()

# Токен бота
BOT_TOKEN = os.getenv('BOT_TOKEN')

# ID группы для отправки сообщений о дивергенциях
NOTIFICATION_GROUP_ID = os.getenv('NOTIFICATION_GROUP_ID')

# Данные для подключения к Postgres
DB_USER = os.getenv('DB_USER')
DB_PASS = os.getenv('DB_PASS')
DB_HOST = os.getenv('DB_HOST')
DB_PORT = os.getenv('DB_PORT')
DB_NAME = os.getenv('DB_NAME')

# Строка подключения к PostgreSQL
POSTGRES_URI = f"postgresql+asyncpg://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# API ключи Binance
BINANCE_API_KEY = os.getenv("BINANCE_API_KEY")
BINANCE_API_SECRET = os.getenv("BINANCE_API_SECRET")

# Список ID суперадминов
SUPERADMIN_IDS = list(map(int, os.getenv('SUPERADMIN_IDS', '').split(',')))

# Интервал проверки дивергенции (в секундах)
CHECK_INTERVAL = int(os.getenv('CHECK_INTERVAL', '3600'))

# Порог дивергенции по умолчанию (в процентах)
DEFAULT_DIVERGENCE_THRESHOLD = float(os.getenv('DEFAULT_DIVERGENCE_THRESHOLD', '5.0'))