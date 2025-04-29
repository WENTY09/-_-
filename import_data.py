import json
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
import os

# Загрузка переменных окружения
load_dotenv()

# Подключение к базе данных
engine = create_engine(os.environ.get("DATABASE_URL"))

# Функция для импорта данных из JSON файла
def import_table_data(table_name, json_file):
    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    if not data:
        print(f"Нет данных для импорта в таблицу {table_name}")
        return
    
    # Получаем список колонок из первого элемента
    columns = list(data[0].keys())
    columns_str = ', '.join(columns)
    values_placeholder = ', '.join(['%s' for _ in columns])
    
    # Создаем SQL запрос
    query = f"INSERT INTO {table_name} ({columns_str}) VALUES ({values_placeholder})"
    
    # Подготавливаем данные для вставки
    values = [[row[col] for col in columns] for row in data]
    
    # Выполняем запрос
    with engine.connect() as conn:
        for value_set in values:
            conn.execute(text(query), value_set)
        conn.commit()
    
    print(f"Импортировано {len(data)} записей в таблицу {table_name}")

# Импортируем данные из всех JSON файлов
tables = {
    'users': 'users.json',
    'shop_items': 'shop_items.json',
    'buffs': 'buffs.json',
    'admins': 'admins.json',
    'admin_login_attempts': 'admin_login_attempts.json'
}

for table, json_file in tables.items():
    try:
        import_table_data(table, json_file)
    except Exception as e:
        print(f"Ошибка при импорте данных в таблицу {table}: {str(e)}")

print("Импорт данных завершен") 