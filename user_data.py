"""
User Data Module

This module manages user data using SQLAlchemy models.
It provides functions for retrieving, updating, and manipulating user data.
"""
import json
import os
import time
import random
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional, Any
from flask import Flask
from models import db, User, Buff, ShopItem, Stats
from config import (
    DATABASE_URL,
    DATA_DIR,
    USER_DATA_FILE,
    SHOP_DATA_FILE,
    STATS_DATA_FILE,
    SQLALCHEMY_TRACK_MODIFICATIONS,
    SQLALCHEMY_ENGINE_OPTIONS
)

# Create Flask app for database context
app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URL
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = SQLALCHEMY_ENGINE_OPTIONS
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = SQLALCHEMY_TRACK_MODIFICATIONS

# Initialize database
db.init_app(app)

# Create data directory if it doesn't exist
os.makedirs(DATA_DIR, exist_ok=True)

def _load_shop_items():
    """Load shop items from JSON file or use defaults."""
    default_items = [
        {
            "item_id": "hyper_buff",
            "name": "Гипер Бафф",
            "description": "Повышает доход на 50%",
            "price": 2750,
            "bonus": 0.5,
            "duration": 40,
            "image": "assets/shop/IMG_1914.jpeg"
        },
        {
            "item_id": "super_buff",
            "name": "Супер Бафф",
            "description": "Повышает доход на 15%",
            "price": 850,
            "bonus": 0.15,
            "duration": 30,
            "image": "assets/shop/IMG_2282.jpeg"
        },
        {
            "item_id": "mega_buff",
            "name": "Мега Бафф",
            "description": "Повышает доход на 25%",
            "price": 1800,
            "bonus": 0.25,
            "duration": 30,
            "image": "assets/shop/IMG_2283.jpeg"
        },
        {
            "item_id": "ultra_buff",
            "name": "Ультра Бафф",
            "description": "Повышает доход на 35%",
            "price": 2200,
            "bonus": 0.35,
            "duration": 35,
            "image": "assets/shop/IMG_2284.jpeg"
        }
    ]
    
    # Try to load from JSON file
    if os.path.exists(SHOP_DATA_FILE):
        try:
            with open(SHOP_DATA_FILE, 'r', encoding='utf-8') as f:
                items = json.load(f)
                if items and len(items) > 0:
                    return items
        except Exception as e:
            print(f"Error loading shop items from file: {e}")
    
    # Save default items to file
    try:
        with open(SHOP_DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(default_items, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Error saving default shop items to file: {e}")
    
    return default_items

def _save_user_data_to_file():
    """Save all user data to file for Beget hosting."""
    try:
        with app.app_context():
            users = User.query.all()
            
            # Convert users to dictionary
            user_data = {}
            for user in users:
                # Get active buffs
                active_buffs = []
                for buff in user.buffs:
                    if buff.expires_at > time.time():
                        active_buffs.append(buff.to_dict())
                
                # Create user dictionary
                user_data[str(user.telegram_id)] = {
                    "username": user.username,
                    "deliveries": user.deliveries,
                    "money": user.money,
                    "experience": user.experience,
                    "last_delivery": user.last_delivery,
                    "blocked": user.blocked,
                    "created_at": user.created_at,
                    "buffs": active_buffs
                }
            
            # Save to file
            with open(USER_DATA_FILE, 'w', encoding='utf-8') as f:
                json.dump(user_data, f, ensure_ascii=False, indent=2)
                
    except Exception as e:
        print(f"Error saving user data to file: {e}")

def _save_stats_to_file():
    """Save stats to file for Beget hosting."""
    try:
        with app.app_context():
            stats = Stats.query.first()
            
            if not stats:
                return
            
            # Convert stats to dictionary
            stats_data = {
                "total_users": stats.total_users,
                "total_deliveries": stats.total_deliveries,
                "total_money": stats.total_money,
                "updated_at": stats.updated_at
            }
            
            # Save to file
            with open(STATS_DATA_FILE, 'w', encoding='utf-8') as f:
                json.dump(stats_data, f, ensure_ascii=False, indent=2)
                
    except Exception as e:
        print(f"Error saving stats to file: {e}")

def init_shop_items():
    """Initialize shop items in the database if they don't exist."""
    with app.app_context():
        # Check if shop items already exist
        if ShopItem.query.count() > 0:
            return
        
        # Load shop items
        items = _load_shop_items()
        
        # Add items to database
        for item_data in items:
            item = ShopItem(
                item_id=item_data["item_id"],
                name=item_data["name"],
                description=item_data["description"],
                price=item_data["price"],
                bonus=item_data["bonus"],
                duration=item_data["duration"],
                is_active=True
            )
            db.session.add(item)
        
        db.session.commit()

def init_stats():
    """Initialize stats in the database if they don't exist."""
    with app.app_context():
        # Check if stats already exist
        if Stats.query.count() > 0:
            return
        
        # Create new stats record
        stats = Stats(
            total_users=0,
            total_deliveries=0,
            total_money=0,
            updated_at=time.time()
        )
        db.session.add(stats)
        db.session.commit()

def initialize_database():
    """Initialize the database with required data."""
    with app.app_context():
        # Import models to make sure tables are created
        import models
        
        # Initialize shop items
        init_shop_items()
        
        # Initialize stats
        init_stats()

def get_user_data(telegram_id: int) -> Dict[str, Any]:
    """Get user data or initialize if it doesn't exist."""
    with app.app_context():
        # Convert to string for database lookup
        str_telegram_id = str(telegram_id)
        
        try:
        # Get user from database
        user = User.query.filter_by(telegram_id=str_telegram_id).first()
        
        # Create new user if not found
        if not user:
            user = User(
                telegram_id=str_telegram_id,
                username=f"Курьер {str_telegram_id[-4:]}",
                deliveries=0,
                money=0,
                experience=0,
                last_delivery=0,
                    blocked=False,
                    created_at=time.time()
            )
            db.session.add(user)
            db.session.commit()
            
            # Update stats
            update_stats(new_user=True)
        
        # Get active buffs
        active_buffs = []
        now = time.time()
        for buff in user.buffs:
            if buff.expires_at > now:
                active_buffs.append(buff.to_dict())
        
        # Convert to dictionary
        user_data = user.to_dict()
        user_data["active_buffs"] = active_buffs
        
        return user_data
            
        except Exception as e:
            print(f"Error in get_user_data: {e}")
            # If there was an error, rollback the session
            db.session.rollback()
            raise

def update_user_data(telegram_id: int, deliveries: int, earnings: int) -> Tuple[int, int]:
    """
    Update user data after a delivery.
    
    Returns:
        Tuple of (original_earnings, buffed_earnings)
    """
    with app.app_context():
        try:
        # Get user data
        str_telegram_id = str(telegram_id)
        user = User.query.filter_by(telegram_id=str_telegram_id).first()
        
        if not user:
            # Create new user if not found
            user = User(
                telegram_id=str_telegram_id,
                username=f"Курьер {str_telegram_id[-4:]}",
                deliveries=0,
                money=0,
                experience=0,
                last_delivery=0,
                    blocked=False,
                    created_at=time.time()
            )
            db.session.add(user)
            db.session.commit()
        
        # Calculate earnings with active buffs
        multiplier = get_active_earnings_multiplier(telegram_id)
        original_earnings = earnings
        buffed_earnings = int(earnings * (1 + multiplier))
        
        # Update user data
        user.deliveries += deliveries
        user.money += buffed_earnings
        user.experience += random.randint(1, 3)  # Random experience gain
        user.last_delivery = time.time()
        
        # Save to database
        db.session.commit()
        
        # Update stats
        update_stats(deliveries=deliveries, earnings=buffed_earnings)
        
        # Save to file for Beget hosting
        _save_user_data_to_file()
        
        return original_earnings, buffed_earnings
            
        except Exception as e:
            print(f"Error in update_user_data: {e}")
            # If there was an error, rollback the session
            db.session.rollback()
            raise

def can_deliver(telegram_id: int) -> Tuple[bool, Optional[timedelta]]:
    """Check if a user can make a delivery (2-minute cooldown)."""
    with app.app_context():
        # Convert to string for database lookup
        str_telegram_id = str(telegram_id)
        
        # Get user from database
        user = User.query.filter_by(telegram_id=str_telegram_id).first()
        
        if not user or not user.last_delivery:
            return True, None
        
        # Check if user is blocked
        if user.blocked:
            return False, None
        
        # Check cooldown
        cooldown = timedelta(minutes=2)
        last_delivery_time = datetime.fromtimestamp(user.last_delivery)
        now = datetime.now()
        time_passed = now - last_delivery_time
        
        if time_passed < cooldown:
            time_remaining = cooldown - time_passed
            return False, time_remaining
        
        return True, None

def get_top_users(limit: int = 5) -> List[Tuple[int, str, int]]:
    """Get the top users by number of deliveries."""
    with app.app_context():
        # Get top users from database
        top_users = User.query.order_by(User.deliveries.desc()).limit(limit).all()
        
        # Convert to list of tuples
        results = []
        for i, user in enumerate(top_users):
            results.append((i+1, user.username, user.deliveries))
        
        return results

def get_shop_item(index: int) -> Dict[str, Any]:
    """Get shop item by index."""
    with app.app_context():
        # Get all active shop items
        items = ShopItem.query.filter_by(is_active=True).all()
        
        # If no items, initialize shop items
        if not items:
            init_shop_items()
            items = ShopItem.query.filter_by(is_active=True).all()
        
        # Make sure index is within bounds
        item_count = len(items)
        if item_count == 0:
            return None
        
        # Ensure index is within bounds using modulo
        item_index = index % item_count
        item = items[item_index]
        
        # Convert to dictionary
        item_data = item.to_dict()
        
        # Add image path if available
        shop_items = _load_shop_items()
        for shop_item in shop_items:
            if shop_item["item_id"] == item.item_id:
                item_data["image"] = shop_item.get("image", "")
                break
        
        return item_data

def get_all_shop_items() -> List[Dict[str, Any]]:
    """Get all shop items."""
    with app.app_context():
        # Get all active shop items
        items = ShopItem.query.filter_by(is_active=True).all()
        
        # If no items, initialize shop items
        if not items:
            init_shop_items()
            items = ShopItem.query.filter_by(is_active=True).all()
        
        # Convert to list of dictionaries
        results = []
        shop_items = _load_shop_items()
        
        for item in items:
            item_data = item.to_dict()
            
            # Add image path if available
            for shop_item in shop_items:
                if shop_item["item_id"] == item.item_id:
                    item_data["image"] = shop_item.get("image", "")
                    break
            
            results.append(item_data)
        
        return results

def get_shop_items_count() -> int:
    """Get the number of shop items."""
    with app.app_context():
        # Get count of active shop items
        count = ShopItem.query.filter_by(is_active=True).count()
        
        # If no items, initialize shop items
        if count == 0:
            init_shop_items()
            count = ShopItem.query.filter_by(is_active=True).count()
        
        return count

def purchase_buff(telegram_id: int, item_index: int) -> Tuple[bool, str]:
    """
    Attempt to purchase a buff for the user.
    
    Returns:
        Tuple of (success, message)
    """
    with app.app_context():
        # Get user
        str_telegram_id = str(telegram_id)
        user = User.query.filter_by(telegram_id=str_telegram_id).first()
        
        if not user:
            return False, "❌ Пользователь не найден."
        
        # Get shop item
        item_data = get_shop_item(item_index)
        
        if not item_data:
            return False, "❌ Предмет не найден."
        
        # Check if user has enough money
        if user.money < item_data["price"]:
            return False, f"❌ Недостаточно денег! Нужно: {item_data['price']} руб."
        
        # Get the actual shop item
        item = ShopItem.query.filter_by(item_id=item_data["item_id"]).first()
        
        if not item:
            return False, "❌ Предмет не найден в базе данных."
        
        # Subtract cost
        user.money -= item.price
        
        # Add buff
        expires_at = time.time() + (item.duration * 60)
        
        buff = Buff(
            user_id=user.id,
            buff_type=item.item_id,
            name=item.name,
            bonus=item.bonus,
            expires_at=expires_at
        )
        
        db.session.add(buff)
        db.session.commit()
        
        # Update stats
        update_stats(buffs_purchased=1)
        
        # Save to file for Beget hosting
        _save_user_data_to_file()
        
        return True, f"✅ Вы приобрели {item.name} на {item.duration} минут!"

def get_active_earnings_multiplier(telegram_id: int) -> float:
    """
    Calculate the total earnings multiplier from all active buffs.
    
    Returns:
        Float multiplier (e.g., 0.25 for 25% increase)
    """
    with app.app_context():
        # Get user
        str_telegram_id = str(telegram_id)
        user = User.query.filter_by(telegram_id=str_telegram_id).first()
        
        if not user:
            return 0.0
        
        # Get active buffs
        now = time.time()
        active_buffs = Buff.query.filter(
            Buff.user_id == user.id,
            Buff.expires_at > now
        ).all()
        
        # Calculate total multiplier
        total_multiplier = sum(buff.bonus for buff in active_buffs)
        
        return total_multiplier

def get_active_buffs_info(telegram_id: int) -> List[Dict[str, Any]]:
    """
    Get information about active buffs for display purposes.
    
    Returns:
        List of active buffs with name and remaining time
    """
    with app.app_context():
        # Get user
        str_telegram_id = str(telegram_id)
        user = User.query.filter_by(telegram_id=str_telegram_id).first()
        
        if not user:
            return []
        
        # Get active buffs
        now = time.time()
        active_buffs = Buff.query.filter(
            Buff.user_id == user.id,
            Buff.expires_at > now
        ).all()
        
        # Format buff information
        buff_info = []
        for buff in active_buffs:
            remaining_seconds = int(buff.expires_at - now)
            minutes, seconds = divmod(remaining_seconds, 60)
            
            buff_info.append({
                "name": buff.name,
                "bonus": int(buff.bonus * 100),
                "remaining_time": f"{minutes}м {seconds}с"
            })
        
        return buff_info

def update_stats(new_user=False, deliveries=0, earnings=0, buffs_purchased=0):
    """Update global statistics."""
    with app.app_context():
        # Get stats
        stats = Stats.query.first()
        
        if not stats:
            # Create new stats record
            stats = Stats(
                total_users=0,
                total_deliveries=0,
                total_money=0,
                updated_at=time.time()
            )
            db.session.add(stats)
        
        # Update stats
        if new_user:
            stats.total_users += 1
        
        stats.total_deliveries += deliveries
        stats.total_money += earnings
        stats.updated_at = time.time()
        
        db.session.commit()
        
        # Save to file for Beget hosting
        _save_stats_to_file()

def is_bot_active() -> bool:
    """Проверяет, активен ли бот."""
    with app.app_context():
        stats = Stats.query.first()
        if not stats:
            return True  # По умолчанию бот активен
        return not getattr(stats, 'is_disabled', False)

def set_bot_state(active: bool) -> bool:
    """
    Устанавливает состояние бота (включен/выключен).
    
    Returns:
        bool: True если состояние успешно изменено, False в случае ошибки
    """
    with app.app_context():
        try:
            stats = Stats.query.first()
            if not stats:
                stats = Stats(
                    total_users=0,
                    total_deliveries=0,
                    total_money=0,
                    updated_at=time.time(),
                    is_disabled=not active
                )
                db.session.add(stats)
            else:
                stats.is_disabled = not active
            
            db.session.commit()
            _save_stats_to_file()
            return True
        except Exception as e:
            print(f"Error setting bot state: {e}")
            db.session.rollback()
            return False

# Initialize random module
import random