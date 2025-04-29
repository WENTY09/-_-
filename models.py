"""
Database models for the Delivery Bot
"""
import time
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class User(db.Model):
    """User model representing a Telegram user."""
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    telegram_id = db.Column(db.String(32), unique=True, nullable=False)
    username = db.Column(db.String(128), nullable=False)
    deliveries = db.Column(db.Integer, default=0)
    money = db.Column(db.Integer, default=0)
    experience = db.Column(db.Integer, default=0)
    last_delivery = db.Column(db.Float, default=0)
    blocked = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.Float, default=time.time)
    is_admin = db.Column(db.Boolean, default=False)
    
    # Relationships
    buffs = db.relationship("Buff", backref="user", lazy=True)

    def to_dict(self):
        """Convert user object to dictionary."""
        return {
            "id": self.id,
            "telegram_id": self.telegram_id,
            "username": self.username,
            "deliveries": self.deliveries,
            "money": self.money,
            "experience": self.experience,
            "last_delivery": self.last_delivery,
            "blocked": self.blocked,
            "created_at": self.created_at,
            "is_admin": self.is_admin
        }

class Buff(db.Model):
    """Buff model representing active user buffs."""
    __tablename__ = 'buffs'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    buff_type = db.Column(db.String(32), nullable=False)
    name = db.Column(db.String(128), nullable=False)
    bonus = db.Column(db.Float, nullable=False)
    expires_at = db.Column(db.Float, nullable=False)
    created_at = db.Column(db.Float, default=time.time)
    
    def to_dict(self):
        """Convert buff object to dictionary."""
        remaining_seconds = max(0, int(self.expires_at - time.time()))
        minutes, seconds = divmod(remaining_seconds, 60)
        
        return {
            "id": self.id,
            "user_id": self.user_id,
            "buff_type": self.buff_type,
            "name": self.name,
            "bonus": self.bonus,
            "expires_at": self.expires_at,
            "created_at": self.created_at,
            "remaining_time": f"{minutes} мин. {seconds} сек."
        }

class ShopItem(db.Model):
    """Shop item model."""
    __tablename__ = 'shop_items'

    id = db.Column(db.Integer, primary_key=True)
    item_id = db.Column(db.String(32), unique=True, nullable=False)
    name = db.Column(db.String(128), nullable=False)
    description = db.Column(db.String(256))
    price = db.Column(db.Integer, nullable=False)
    bonus = db.Column(db.Float, nullable=False)
    duration = db.Column(db.Integer, nullable=False)  # in minutes
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.Float, default=time.time)
    updated_at = db.Column(db.Float, default=time.time, onupdate=time.time)
    
    def to_dict(self):
        """Convert shop item object to dictionary."""
        return {
            "id": self.id,
            "item_id": self.item_id,
            "name": self.name,
            "description": self.description,
            "price": self.price,
            "bonus": self.bonus,
            "duration": self.duration,
            "is_active": self.is_active,
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }

class Stats(db.Model):
    """Statistics model."""
    __tablename__ = 'stats'

    id = db.Column(db.Integer, primary_key=True)
    total_users = db.Column(db.Integer, default=0)
    total_deliveries = db.Column(db.Integer, default=0)
    total_money = db.Column(db.Integer, default=0)
    updated_at = db.Column(db.Float, default=time.time)
    is_disabled = db.Column(db.Boolean, default=False)
    
    def to_dict(self):
        """Convert stats object to dictionary."""
        return {
            "id": self.id,
            "total_users": self.total_users,
            "total_deliveries": self.total_deliveries,
            "total_money": self.total_money,
            "updated_at": self.updated_at,
            "is_disabled": self.is_disabled
        }

class Admin(db.Model):
    """Model for storing admin data."""
    __tablename__ = 'admins'

    id = db.Column(db.Integer, primary_key=True)
    telegram_id = db.Column(db.String(20), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # owner, admin, moderator
    permissions = db.Column(db.JSON, nullable=False)  # JSON of permissions
    added_by = db.Column(db.String(20), nullable=False)
    added_at = db.Column(db.Float, default=time.time)
    username = db.Column(db.String(100), nullable=True)  # Admin username for web panel
    password_hash = db.Column(db.String(256), nullable=True)  # Hashed password for web panel
    
    def to_dict(self):
        """Convert admin to dictionary."""
        return {
            "id": self.id,
            "telegram_id": self.telegram_id,
            "name": self.name,
            "role": self.role,
            "permissions": self.permissions,
            "username": self.username
        }

class AdminLoginAttempt(db.Model):
    """Model for tracking admin login attempts (for security)."""
    __tablename__ = 'admin_login_attempts'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), nullable=False)
    ip_address = db.Column(db.String(100), nullable=True)
    success = db.Column(db.Boolean, default=False)
    timestamp = db.Column(db.Float, default=time.time)
    
    def to_dict(self):
        """Convert login attempt to dictionary."""
        return {
            "id": self.id,
            "username": self.username,
            "ip_address": self.ip_address,
            "success": self.success,
            "timestamp": self.timestamp
        }
