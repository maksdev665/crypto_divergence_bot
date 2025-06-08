# crypto_divergence_bot
Криптовалютный Трейдинг Бот для Отслеживания Дивергенций

Структура проекта

```
crypto_divergence_bot/
├── alembic/                      # Миграции базы данных
│   └── versions/
├── app/
│   ├── __init__.py
│   ├── bot.py                    # Основной файл бота
│   ├── config.py                 # Конфигурация проекта
│   ├── database/
│   │   ├── __init__.py
│   │   ├── base.py               # Базовый класс модели
│   │   ├── engine.py             # Настройка подключения к БД
│   │   └── models/
│   │       ├── __init__.py
│   │       ├── admin.py          # Модель администратора
│   │       ├── currency_pair.py  # Модель валютной пары
│   │       ├── divergence.py     # Модель обнаруженной дивергенции
│   │       └── settings.py       # Модель настроек бота
│   ├── services/
│   │   ├── __init__.py
│   │   ├── binance_api.py        # Сервис для работы с Binance API
│   │   ├── divergence.py         # Логика анализа дивергенций
│   │   └── notifications.py      # Сервис для отправки уведомлений
│   ├── handlers/
│   │   ├── __init__.py
│   │   ├── admin/
│   │   │   ├── __init__.py
│   │   │   ├── admin_panel.py    # Основная панель админа
│   │   │   ├── pairs.py          # Управление валютными парами
│   │   │   └── settings.py       # Настройки бота
│   │   └── common.py             # Общие обработчики
│   ├── keyboards/
│   │   ├── __init__.py
│   │   ├── admin_kb.py           # Клавиатуры для админа
│   │   └── inline_kb.py          # Инлайн клавиатуры
│   ├── middlewares/
│   │   ├── __init__.py
│   │   └── admin_middleware.py   # Проверка прав администратора
│   └── utils/
│       ├── __init__.py
│       └── states.py             # Состояния для FSM
├── migrations/                   # Скрипты миграций
├── .env.example                  # Пример файла с переменными окружения
├── .gitignore
├── alembic.ini                   # Конфигурация Alembic
├── docker-compose.yml            # Конфигурация Docker
├── Dockerfile
├── requirements.txt              # Зависимости проекта
└── run.py                        # Точка входа в приложение
```