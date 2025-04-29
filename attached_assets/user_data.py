"""
Module for managing user data.
"""
import os
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional, Any

# Path to save user data
DATA_FILE = "data/user_data.json"

# Shop items with their details
SHOP_ITEMS = [
    {
        "id": 0,
        "name": "Гипер Бафф",
        "description": "Увеличивает доход от доставок на 50%",
        "price": 2750,
        "bonus": 0.5,  # 50% increase
        "duration": 40  # in minutes
    },
    {
        "id": 1,
        "name": "Супер Бафф",
        "description": "Увеличивает доход от доставок на 15%",
        "price": 850,
        "bonus": 0.15,  # 15% increase
        "duration": 30  # in minutes
    },
    {
        "id": 2,
        "name": "Мега Бафф",
        "description": "Увеличивает доход от доставок на 25%",
        "price": 1800,
        "bonus": 0.25,  # 25% increase
        "duration": 30  # in minutes
    }
]

# Global variable to store all user data
USER_DATA = {}

# Admin roles
ROLE_OWNER = "owner"
ROLE_ADMIN = "admin"

# Default admin list with owner
DEFAULT_ADMINS = {
    "6999938953": {
        "role": ROLE_OWNER,
        "name": "@white_wenty",
        "permissions": {
            "block_users": True,
            "add_money": True,
            "remove_money": True,
            "give_items": True,
            "broadcast": True,
            "view_users": True,
            "manage_admins": True
        }
    }
}

def _load_data() -> None:
    """Load user data from file if it exists."""
    global USER_DATA
    
    # Create data directory if it doesn't exist
    os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)
    
    try:
        if os.path.exists(DATA_FILE):
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                USER_DATA = json.load(f)
                
                # Make sure to check for admin key
                if "_admins" not in USER_DATA:
                    USER_DATA["_admins"] = DEFAULT_ADMINS
        else:
            # If no existing data, initialize with default admins
            USER_DATA = {"_admins": DEFAULT_ADMINS}
    except Exception as e:
        print(f"Error loading user data: {e}")
        USER_DATA = {"_admins": DEFAULT_ADMINS}

def _save_data() -> None:
    """Save user data to file."""
    try:
        # Create data directory if it doesn't exist
        os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)
        
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(USER_DATA, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Error saving user data: {e}")

def get_user_data(user_id: int) -> Dict[str, Any]:
    """Get user data or initialize if it doesn't exist."""
    global USER_DATA
    
    # Load data if it's empty
    if not USER_DATA:
        _load_data()
    
    # Convert user_id to string for JSON compatibility
    user_id_str = str(user_id)
    
    # Initialize user data if it doesn't exist
    if user_id_str not in USER_DATA:
        USER_DATA[user_id_str] = {
            "username": "Курьер",  # Default name
            "deliveries": 0,       # Number of completed deliveries
            "money": 0,            # Money earned
            "last_delivery": 0,    # Timestamp of last delivery
            "buffs": []            # Active buffs
        }
        _save_data()
    
    # Prune expired buffs
    _prune_expired_buffs(user_id_str)
    
    return USER_DATA[user_id_str]

def update_user_data(user_id: int, deliveries: int, earnings: int) -> Tuple[int, int]:
    """
    Update user data after a delivery.
    
    Returns:
        Tuple of (original_earnings, buffed_earnings)
    """
    # Get user data
    user_data = get_user_data(user_id)
    
    # Calculate earnings with active buffs
    multiplier = get_active_earnings_multiplier(user_id)
    original_earnings = earnings
    buffed_earnings = int(earnings * (1 + multiplier))
    
    # Update user data
    user_data['deliveries'] += deliveries
    user_data['money'] += buffed_earnings
    user_data['last_delivery'] = time.time()
    
    # Save data
    _save_data()
    
    return original_earnings, buffed_earnings

def can_deliver(user_id: int) -> Tuple[bool, Optional[timedelta]]:
    """Check if a user can make a delivery (7-minute cooldown)."""
    user_data = get_user_data(user_id)
    
    # Check if user is blocked
    if user_data.get('blocked', False):
        return False, None
    
    if not user_data['last_delivery']:
        return True, None
    
    # Calculate time since last delivery
    last_time = datetime.fromtimestamp(user_data['last_delivery'])
    current_time = datetime.now()
    time_passed = current_time - last_time
    
    # 7-minute cooldown as requested
    cooldown = timedelta(minutes=7)
    
    if time_passed >= cooldown:
        return True, None
    else:
        return False, cooldown - time_passed

def get_top_users(limit: int = 5) -> List[Tuple[int, str, int]]:
    """Get the top users by number of deliveries."""
    global USER_DATA
    
    # Load data if it's empty
    if not USER_DATA:
        _load_data()
    
    # Convert to list of tuples (user_id, username, deliveries)
    users = [(int(user_id), data['username'], data['deliveries']) 
             for user_id, data in USER_DATA.items()]
    
    # Sort by deliveries (descending)
    users.sort(key=lambda x: x[2], reverse=True)
    
    # Return top users
    return users[:limit]

def get_shop_item(index: int) -> Dict[str, Any]:
    """Get shop item by index.
    
    First tries to get item from the database.
    If not found, falls back to the static items list.
    """
    from app import app, db
    from models import ShopItem
    
    # Попытка получить товар из базы данных
    if index >= 0:  # Для валидных индексов проверяем базу
        with app.app_context():
            item = db.session.query(ShopItem).filter(
                ShopItem.id == index,
                ShopItem.is_active == True
            ).first()
            
            if item:
                return item.to_dict()
    
    # Если в базе не найдено, используем статический список
    if 0 <= index < len(SHOP_ITEMS):
        return SHOP_ITEMS[index]
    return None

def get_all_shop_items() -> List[Dict[str, Any]]:
    """Get all active shop items from the database."""
    from app import app, db
    from models import ShopItem
    
    # Получаем все активные товары из базы данных
    with app.app_context():
        items = db.session.query(ShopItem).filter(ShopItem.is_active == True).all()
    
    # Преобразуем в словари
    result = [item.to_dict() for item in items]
    
    # Если в базе нет товаров, возвращаем стандартные
    if not result:
        result = SHOP_ITEMS
        
    return result

def add_shop_item(admin_id: int, name: str, description: str, price: int, 
                  bonus: float, duration: int) -> Tuple[bool, str]:
    """Add a new shop item."""
    from app import db
    from models import ShopItem, Admin
    
    # Проверяем, имеет ли администратор права для добавления товаров
    if not is_admin_with_permission(admin_id, "manage_items"):
        return False, "У вас нет прав для управления товарами магазина."
    
    # Валидация данных
    if not name or len(name) < 3:
        return False, "Название товара должно содержать не менее 3 символов."
    
    if not description or len(description) < 5:
        return False, "Описание товара должно содержать не менее 5 символов."
    
    if price <= 0:
        return False, "Цена товара должна быть положительной."
    
    if bonus <= 0:
        return False, "Бонус товара должен быть положительным."
    
    if duration <= 0:
        return False, "Длительность эффекта должна быть положительной."
    
    # Создаем новый товар
    try:
        admin = db.session.query(Admin).filter(Admin.telegram_id == str(admin_id)).first()
        if not admin:
            return False, "Администратор не найден."
        
        new_item = ShopItem(
            name=name,
            description=description,
            price=price,
            bonus=bonus,
            duration=duration,
            is_active=True,
            created_by=str(admin_id)
        )
        
        db.session.add(new_item)
        db.session.commit()
        
        return True, f"Товар '{name}' успешно добавлен в магазин."
    except Exception as e:
        db.session.rollback()
        return False, f"Ошибка при добавлении товара: {e}"

def edit_shop_item(admin_id: int, item_id: int, name: str = None, description: str = None, 
                   price: int = None, bonus: float = None, duration: int = None, 
                   is_active: bool = None) -> Tuple[bool, str]:
    """Edit an existing shop item."""
    from app import db
    from models import ShopItem
    
    # Проверяем, имеет ли администратор права для редактирования товаров
    if not is_admin_with_permission(admin_id, "manage_items"):
        return False, "У вас нет прав для управления товарами магазина."
    
    # Получаем товар из базы данных
    item = db.session.query(ShopItem).filter(ShopItem.id == item_id).first()
    if not item:
        return False, "Товар не найден."
    
    # Обновляем значения, если они указаны
    try:
        if name is not None and len(name) >= 3:
            item.name = name
        elif name is not None:
            return False, "Название товара должно содержать не менее 3 символов."
        
        if description is not None and len(description) >= 5:
            item.description = description
        elif description is not None:
            return False, "Описание товара должно содержать не менее 5 символов."
        
        if price is not None:
            if price <= 0:
                return False, "Цена товара должна быть положительной."
            item.price = price
        
        if bonus is not None:
            if bonus <= 0:
                return False, "Бонус товара должен быть положительным."
            item.bonus = bonus
        
        if duration is not None:
            if duration <= 0:
                return False, "Длительность эффекта должна быть положительной."
            item.duration = duration
        
        if is_active is not None:
            item.is_active = is_active
        
        db.session.commit()
        
        return True, f"Товар '{item.name}' успешно обновлен."
    except Exception as e:
        db.session.rollback()
        return False, f"Ошибка при обновлении товара: {e}"

def delete_shop_item(admin_id: int, item_id: int) -> Tuple[bool, str]:
    """Delete (deactivate) a shop item."""
    from app import db
    from models import ShopItem
    
    # Проверяем, имеет ли администратор права для удаления товаров
    if not is_admin_with_permission(admin_id, "manage_items"):
        return False, "У вас нет прав для управления товарами магазина."
    
    # Получаем товар из базы данных
    item = db.session.query(ShopItem).filter(ShopItem.id == item_id).first()
    if not item:
        return False, "Товар не найден."
    
    # Деактивируем товар вместо удаления
    try:
        item.is_active = False
        db.session.commit()
        
        return True, f"Товар '{item.name}' деактивирован."
    except Exception as e:
        db.session.rollback()
        return False, f"Ошибка при деактивации товара: {e}"

def purchase_buff(user_id: int, item_index: int) -> Tuple[bool, str]:
    """
    Attempt to purchase a buff for the user.
    
    Returns:
        Tuple of (success, message)
    """
    # Get user data and shop item
    user_data = get_user_data(user_id)
    item = get_shop_item(item_index)
    
    if not item:
        return False, "Такой предмет не найден в магазине!"
    
    # Check if user has enough money
    if user_data['money'] < item['price']:
        return False, f"Недостаточно денег! Нужно: {item['price']} руб."
    
    # Deduct money
    user_data['money'] -= item['price']
    
    # Add buff to user's active buffs
    buff = {
        "id": item['id'],
        "name": item['name'],
        "bonus": item['bonus'],
        "expires_at": time.time() + (item['duration'] * 60)  # Convert minutes to seconds
    }
    
    user_data['buffs'].append(buff)
    
    # Save data
    _save_data()
    
    buff_info = {
            'name': item.name,
            'multiplier': item.bonus, 
            'remaining_minutes': item.duration,
            'remaining_seconds': 0
        }
        buff_info['buff_id'] = item.item_id
        
        return True, f"Вы приобрели {item.name} на {item.duration} минут!" {item['name']}! Теперь вы будете получать +{int(item['bonus']*100)}% к доходу от доставок в течение {item['duration']} минут."

def get_active_earnings_multiplier(user_id: int) -> float:
    """
    Calculate the total earnings multiplier from all active buffs.
    
    Returns:
        Float multiplier (e.g., 0.25 for 25% increase)
    """
    user_data = get_user_data(user_id)
    
    # Check for and remove expired buffs
    _prune_expired_buffs(str(user_id))
    
    # Sum up all active buff bonuses
    multiplier = sum(buff['bonus'] for buff in user_data['buffs'])
    
    return multiplier

def get_active_buffs_info(user_id: int) -> List[Dict[str, Any]]:
    """
    Get information about active buffs for display purposes.
    
    Returns:
        List of active buffs with name and remaining time
    """
    user_data = get_user_data(user_id)
    
    # Check for and remove expired buffs
    _prune_expired_buffs(str(user_id))
    
    # Format buff info for display
    result = []
    current_time = time.time()
    
    for buff in user_data['buffs']:
        remaining_seconds = int(buff['expires_at'] - current_time)
        minutes, seconds = divmod(remaining_seconds, 60)
        
        result.append({
            "name": buff['name'],
            "bonus": buff['bonus'],
            "remaining_time": f"{minutes} мин. {seconds} сек."
        })
    
    return result

def _prune_expired_buffs(user_id_str: str) -> None:
    """Remove expired buffs from user data."""
    global USER_DATA
    
    if user_id_str not in USER_DATA:
        return
    
    current_time = time.time()
    USER_DATA[user_id_str]['buffs'] = [
        buff for buff in USER_DATA[user_id_str]['buffs']
        if buff['expires_at'] > current_time
    ]
    
    # Save data if buffs were removed
    _save_data()

def get_system_stats() -> Dict[str, Any]:
    """
    Get statistics about the bot for the dashboard.
    
    Returns:
        Dict with system stats
    """
    global USER_DATA
    
    # Load data if it's empty
    if not USER_DATA:
        _load_data()
    
    total_users = len(USER_DATA)
    total_deliveries = sum(data['deliveries'] for data in USER_DATA.values())
    total_earnings = sum(data['money'] for data in USER_DATA.values())
    
    # Count active buffs across all users
    active_buffs = 0
    current_time = time.time()
    
    for user_id, data in USER_DATA.items():
        for buff in data['buffs']:
            if buff['expires_at'] > current_time:
                active_buffs += 1
    
    return {
        "total_users": total_users,
        "total_deliveries": total_deliveries,
        "total_earnings": total_earnings,
        "active_buffs": active_buffs
    }

# Admin functions
def is_admin(user_id: int) -> bool:
    """Check if a user is an admin."""
    from app import db
    from models import Admin
    
    # Преобразуем числовой ID в строку, так как в базе он хранится как строка
    user_id_str = str(user_id)
    
    # Проверяем наличие админа в базе данных
    admin = db.session.query(Admin).filter(Admin.telegram_id == user_id_str).first()
    
    return admin is not None

def get_admin_permissions(user_id: int) -> Dict[str, bool]:
    """Get admin permissions for a user."""
    from app import db
    from models import Admin
    
    # Преобразуем числовой ID в строку, так как в базе он хранится как строка
    user_id_str = str(user_id)
    
    # Проверяем наличие админа в базе данных
    admin = db.session.query(Admin).filter(Admin.telegram_id == user_id_str).first()
    
    if admin:
        return admin.permissions
    
    return {}

def is_admin_with_permission(user_id: int, permission: str) -> bool:
    """Check if user is admin with a specific permission."""
    permissions = get_admin_permissions(user_id)
    return permissions.get(permission, False)

def add_admin(added_by_id: int, new_admin_id: int, admin_name: str, role: str = ROLE_ADMIN, permissions: Dict[str, bool] = None) -> Tuple[bool, str]:
    """Add a new admin to the system."""
    global USER_DATA
    
    # Check if the user adding is an admin with manage_admins permission
    if not is_admin_with_permission(added_by_id, "manage_admins"):
        return False, "У вас нет прав для управления администраторами."
    
    # Default permissions if none provided
    if permissions is None:
        permissions = {
            "block_users": False,
            "add_money": False,
            "remove_money": False,
            "give_items": False,
            "broadcast": False,
            "view_users": True,
            "manage_admins": False
        }
    
    # Add the new admin
    USER_DATA.setdefault("_admins", {})
    USER_DATA["_admins"][str(new_admin_id)] = {
        "role": role,
        "name": admin_name,
        "permissions": permissions,
        "added_by": str(added_by_id),
        "added_at": time.time()
    }
    
    _save_data()
    return True, f"Администратор {admin_name} успешно добавлен."

def remove_admin(removed_by_id: int, admin_id: int) -> Tuple[bool, str]:
    """Remove an admin from the system."""
    global USER_DATA
    
    # Check if the user removing is an admin with manage_admins permission
    if not is_admin_with_permission(removed_by_id, "manage_admins"):
        return False, "У вас нет прав для управления администраторами."
    
    admin_id_str = str(admin_id)
    
    # Check if admin exists
    if admin_id_str not in USER_DATA.get("_admins", {}):
        return False, "Указанный пользователь не является администратором."
    
    # Cannot remove OWNER
    if USER_DATA["_admins"][admin_id_str]["role"] == ROLE_OWNER:
        return False, "Невозможно удалить владельца бота."
    
    # Remove the admin
    del USER_DATA["_admins"][admin_id_str]
    _save_data()
    
    return True, "Администратор успешно удален."

def update_admin_permissions(updated_by_id: int, admin_id: int, permissions: Dict[str, bool]) -> Tuple[bool, str]:
    """Update an admin's permissions."""
    global USER_DATA
    
    # Check if the user updating is an admin with manage_admins permission
    if not is_admin_with_permission(updated_by_id, "manage_admins"):
        return False, "У вас нет прав для управления администраторами."
    
    admin_id_str = str(admin_id)
    
    # Check if admin exists
    if admin_id_str not in USER_DATA.get("_admins", {}):
        return False, "Указанный пользователь не является администратором."
    
    # Cannot modify OWNER's permissions
    if USER_DATA["_admins"][admin_id_str]["role"] == ROLE_OWNER:
        return False, "Невозможно изменить права владельца бота."
    
    # Update permissions
    USER_DATA["_admins"][admin_id_str]["permissions"].update(permissions)
    _save_data()
    
    return True, "Права администратора успешно обновлены."

def block_user(admin_id: int, user_id: int) -> Tuple[bool, str]:
    """Block a user from using the bot."""
    # Check if admin has permission
    if not is_admin_with_permission(admin_id, "block_users"):
        return False, "У вас нет прав для блокировки пользователей."
    
    user_id_str = str(user_id)
    
    # Check if user exists
    if user_id_str not in USER_DATA:
        return False, "Пользователь не найден."
    
    # Check if user is an admin
    if user_id_str in USER_DATA.get("_admins", {}):
        return False, "Невозможно заблокировать администратора."
    
    # Block the user
    USER_DATA[user_id_str]["blocked"] = True
    _save_data()
    
    return True, f"Пользователь {USER_DATA[user_id_str]['username']} заблокирован."

def unblock_user(admin_id: int, user_id: int) -> Tuple[bool, str]:
    """Unblock a user from using the bot."""
    # Check if admin has permission
    if not is_admin_with_permission(admin_id, "block_users"):
        return False, "У вас нет прав для разблокировки пользователей."
    
    user_id_str = str(user_id)
    
    # Check if user exists
    if user_id_str not in USER_DATA:
        return False, "Пользователь не найден."
    
    # Unblock the user
    USER_DATA[user_id_str]["blocked"] = False
    _save_data()
    
    return True, f"Пользователь {USER_DATA[user_id_str]['username']} разблокирован."

def add_money(admin_id: int, user_id: int, amount: int) -> Tuple[bool, str]:
    """Add money to a user's account."""
    # Check if admin has permission
    if not is_admin_with_permission(admin_id, "add_money"):
        return False, "У вас нет прав для добавления денег."
    
    if amount <= 0:
        return False, "Сумма должна быть положительной."
    
    user_id_str = str(user_id)
    
    # Check if user exists
    if user_id_str not in USER_DATA:
        return False, "Пользователь не найден."
    
    # Add money
    USER_DATA[user_id_str]["money"] += amount
    _save_data()
    
    return True, f"Добавлено {amount} рублей пользователю {USER_DATA[user_id_str]['username']}."

def remove_money(admin_id: int, user_id: int, amount: int) -> Tuple[bool, str]:
    """Remove money from a user's account."""
    # Check if admin has permission
    if not is_admin_with_permission(admin_id, "remove_money"):
        return False, "У вас нет прав для удаления денег."
    
    if amount <= 0:
        return False, "Сумма должна быть положительной."
    
    user_id_str = str(user_id)
    
    # Check if user exists
    if user_id_str not in USER_DATA:
        return False, "Пользователь не найден."
    
    # Check if user has enough money
    if USER_DATA[user_id_str]["money"] < amount:
        USER_DATA[user_id_str]["money"] = 0
        _save_data()
        return True, f"Счет пользователя {USER_DATA[user_id_str]['username']} обнулен."
    
    # Remove money
    USER_DATA[user_id_str]["money"] -= amount
    _save_data()
    
    return True, f"Удалено {amount} рублей у пользователя {USER_DATA[user_id_str]['username']}."

def give_buff(admin_id: int, user_id: int, buff_id: int) -> Tuple[bool, str]:
    """Give a buff to a user."""
    # Check if admin has permission
    if not is_admin_with_permission(admin_id, "give_items"):
        return False, "У вас нет прав для выдачи предметов."
    
    user_id_str = str(user_id)
    
    # Check if user exists
    if user_id_str not in USER_DATA:
        return False, "Пользователь не найден."
    
    # Check if buff exists
    item = get_shop_item(buff_id)
    if not item:
        return False, "Указанный бафф не найден."
    
    # Add buff
    buff = {
        "id": item["id"],
        "name": item["name"],
        "bonus": item["bonus"],
        "expires_at": time.time() + (item["duration"] * 60)  # Convert minutes to seconds
    }
    
    USER_DATA[user_id_str]["buffs"].append(buff)
    _save_data()
    
    return True, f"Бафф {item['name']} выдан пользователю {USER_DATA[user_id_str]['username']}."

def get_all_users() -> List[Dict[str, Any]]:
    """Get a list of all users for admin view."""
    global USER_DATA
    
    if not USER_DATA:
        _load_data()
    
    result = []
    for user_id, data in USER_DATA.items():
        # Skip special keys
        if user_id.startswith("_"):
            continue
        
        result.append({
            "user_id": int(user_id),
            "username": data["username"],
            "deliveries": data["deliveries"],
            "money": data["money"],
            "blocked": data.get("blocked", False),
            "active_buffs": len([b for b in data["buffs"] if b["expires_at"] > time.time()])
        })
    
    return result

def get_user_details(user_id: int) -> Dict[str, Any]:
    """Get detailed information about a user for admin view."""
    user_data = get_user_data(user_id)
    active_buffs = get_active_buffs_info(user_id)
    
    result = {
        "user_id": user_id,
        "username": user_data["username"],
        "deliveries": user_data["deliveries"],
        "money": user_data["money"],
        "blocked": user_data.get("blocked", False),
        "active_buffs": active_buffs,
        "last_delivery_time": datetime.fromtimestamp(user_data["last_delivery"]).strftime("%Y-%m-%d %H:%M:%S") if user_data["last_delivery"] else "Never"
    }
    
    return result

def get_all_admins() -> List[Dict[str, Any]]:
    """Get a list of all admins."""
    global USER_DATA
    
    if not USER_DATA:
        _load_data()
    
    result = []
    for admin_id, data in USER_DATA.get("_admins", {}).items():
        result.append({
            "user_id": int(admin_id),
            "name": data["name"],
            "role": data["role"],
            "permissions": data["permissions"]
        })
    
    return result

def prepare_broadcast(admin_id: int, message_text: str) -> Tuple[bool, str, List[int]]:
    """
    Prepare to broadcast a message to all users.
    
    Returns:
        Tuple of (success, message, list of user IDs to send to)
    """
    # Check if admin has permission
    if not is_admin_with_permission(admin_id, "broadcast"):
        return False, "У вас нет прав для рассылки сообщений.", []
    
    if not message_text or len(message_text) < 5:
        return False, "Сообщение слишком короткое.", []
    
    # Get all active users (excluding special keys and blocked users)
    user_ids = []
    for user_id, data in USER_DATA.items():
        if (not user_id.startswith("_") and 
            not data.get("blocked", False)):
            user_ids.append(int(user_id))
    
    if not user_ids:
        return False, "Нет пользователей для рассылки.", []
    
    return True, f"Подготовлена рассылка для {len(user_ids)} пользователей.", user_ids

# Initialize by loading data
_load_data()