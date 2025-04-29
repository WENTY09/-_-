# Delivery Bot

Telegram бот для системы доставки с возможностью покупки баффов.

## Установка

1. Клонируйте репозиторий:
```bash
git clone <repository_url>
cd delivery-bot
```

2. Создайте виртуальное окружение и активируйте его:
```bash
python -m venv venv
# Windows
venv\Scripts\activate
# Linux/macOS
source venv/bin/activate
```

3. Установите зависимости:
```bash
pip install -r requirements.txt
```

4. Создайте файл `.env` в корневой директории проекта и добавьте следующие переменные:
```
BOT_TOKEN=your_bot_token_here
FLASK_SECRET_KEY=your_secret_key_here
```

## Запуск

1. Инициализируйте базу данных:
```bash
python -c "from user_data import initialize_database; initialize_database()"
```

2. Запустите бота:
```bash
python bot.py
```

## Команды бота

- `/start` - Начать работу с ботом
- `/help` - Показать список команд
- `/deliver` - Сделать доставку
- `/profile` - Посмотреть профиль
- `/top` - Топ курьеров
- `/shop` - Магазин баффов
- `/buffs` - Активные баффы
- `/buy <номер>` - Купить предмет из магазина

## Структура проекта

- `bot.py` - Основной файл бота
- `user_data.py` - Управление данными пользователей
- `models.py` - Модели базы данных
- `config.py` - Конфигурация проекта
- `requirements.txt` - Зависимости проекта
- `.env` - Переменные окружения (не включен в репозиторий)
- `data/` - Директория для хранения данных
  - `user_data.json` - Данные пользователей
  - `shop_items.json` - Предметы магазина
  - `stats.json` - Статистика 