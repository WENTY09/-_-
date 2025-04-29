"""
Models for the Telegram delivery bot.
"""
import time
from sqlalchemy import Column, Integer, String, Float, Boolean, ForeignKey, Text, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()
Base = db.Model

class User(Base):
    """User model for storing telegram users data."""
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    telegram_id = Column(String(20), unique=True, nullable=False)
    username = Column(String(100), default="Курьер")
    deliveries = Column(Integer, default=0)
    money = Column(Integer, default=0)
    last_delivery = Column(Float, default=0)
    blocked = Column(Boolean, default=False)
    created_at = Column(Float, default=time.time)
    
    # Relationships
    buffs = relationship("Buff", backref="user", cascade="all, delete-orphan")

    def to_dict(self):
        """Convert user to dictionary."""
        return {
            "user_id": self.telegram_id,
            "username": self.username,
            "deliveries": self.deliveries,
            "money": self.money,
            "blocked": self.blocked,
            "last_delivery": self.last_delivery,
            "last_delivery_time": self._format_last_delivery_time()
        }
    
    def _format_last_delivery_time(self):
        """Format last delivery time for display."""
        if not self.last_delivery:
            return "Еще не делал доставок"
        
        # Convert timestamp to readable format
        from datetime import datetime
        dt = datetime.fromtimestamp(self.last_delivery)
        return dt.strftime("%d.%m.%Y %H:%M:%S")

class Buff(Base):
    """Model for storing user buffs."""
    __tablename__ = 'buffs'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    buff_type = Column(Integer, nullable=False)  # References the buff type (0, 1, 2)
    name = Column(String(100), nullable=False)
    bonus = Column(Float, nullable=False)
    expires_at = Column(Float, nullable=False)
    created_at = Column(Float, default=time.time)
    
    def to_dict(self):
        """Convert buff to dictionary."""
        remaining_seconds = max(0, int(self.expires_at - time.time()))
        minutes, seconds = divmod(remaining_seconds, 60)
        
        return {
            "id": self.buff_type,
            "name": self.name,
            "bonus": self.bonus,
            "expires_at": self.expires_at,
            "remaining_time": f"{minutes} мин. {seconds} сек."
        }

class Admin(Base):
    """Model for storing admin data."""
    __tablename__ = 'admins'

    id = Column(Integer, primary_key=True)
    telegram_id = Column(String(20), unique=True, nullable=False)
    name = Column(String(100), nullable=False)
    role = Column(String(20), nullable=False)  # owner, admin, moderator
    permissions = Column(JSON, nullable=False)  # JSON of permissions
    added_by = Column(String(20), nullable=False)
    added_at = Column(Float, default=time.time)
    
    def to_dict(self):
        """Convert admin to dictionary."""
        return {
            "user_id": self.telegram_id,
            "name": self.name,
            "role": self.role,
            "permissions": self.permissions
        }


class ShopItem(Base):
    """Model for storing shop items."""
    __tablename__ = 'shop_items'

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    description = Column(String(200), nullable=False)
    price = Column(Integer, nullable=False)
    bonus = Column(Float, nullable=False)  # Percentage bonus as decimal (0.15 = 15%)
    duration = Column(Integer, nullable=False)  # Duration in minutes
    is_active = Column(Boolean, default=True)
    created_by = Column(String(20), nullable=False)  # Telegram ID of admin who created item
    created_at = Column(Float, default=time.time)
    updated_at = Column(Float, default=time.time, onupdate=time.time)
    
    def to_dict(self):
        """Convert shop item to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "price": self.price,
            "bonus": self.bonus,
            "duration": self.duration,
            "is_active": self.is_active
        }