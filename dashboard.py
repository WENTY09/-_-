"""
Dashboard Module for Delivery Bot

This module provides a web dashboard for monitoring the Telegram bot.
"""
import os
import json
import time
import logging
import psutil
from datetime import datetime
from flask import Blueprint, render_template, jsonify, redirect, url_for
from models import db, User, Buff, ShopItem, Stats

# Configure logging
logger = logging.getLogger(__name__)

# Create blueprint
dashboard_bp = Blueprint('dashboard', __name__, url_prefix='/dashboard')

@dashboard_bp.route('/')
def index():
    """Render the main dashboard page."""
    return render_template('index.html')

@dashboard_bp.route('/stats')
def stats_page():
    """Render the detailed statistics page."""
    return render_template('stats.html')

@dashboard_bp.route('/users')
def users_page():
    """Render the users page."""
    return render_template('users.html')

@dashboard_bp.route('/api/stats')
def api_stats():
    """API endpoint for getting real-time stats."""
    try:
        # Get database stats
        total_users = User.query.count()
        total_deliveries = db.session.query(db.func.sum(User.deliveries)).scalar() or 0
        total_money = db.session.query(db.func.sum(User.money)).scalar() or 0
        active_buffs = Buff.query.filter(Buff.expires_at > time.time()).count()
        
        # Get system stats
        cpu_percent = psutil.cpu_percent()
        memory = psutil.virtual_memory()
        memory_percent = memory.percent
        
        # Get disk usage
        disk = psutil.disk_usage('/')
        disk_percent = disk.percent
        
        # Get uptime (in seconds)
        try:
            uptime = int(time.time() - psutil.boot_time())
        except Exception:
            uptime = 0
        
        # Format uptime
        days, remainder = divmod(uptime, 86400)
        hours, remainder = divmod(remainder, 3600)
        minutes, seconds = divmod(remainder, 60)
        uptime_str = f"{days}d {hours}h {minutes}m {seconds}s"
        
        # Format results
        stats = {
            "system": {
                "cpu": cpu_percent,
                "memory": memory_percent,
                "disk": disk_percent,
                "uptime": uptime_str
            },
            "bot": {
                "total_users": total_users,
                "total_deliveries": total_deliveries,
                "total_earnings": total_money,
                "active_buffs": active_buffs
            }
        }
        
        return jsonify(stats)
    except Exception as e:
        logger.error(f"Error fetching stats: {e}")
        return jsonify({"error": str(e)}), 500

@dashboard_bp.route('/api/users')
def api_users():
    """API endpoint for getting user data."""
    try:
        # Get all users
        users = User.query.order_by(User.deliveries.desc()).limit(100).all()
        
        # Format results
        user_list = []
        for user in users:
            # Count active buffs for user
            active_buffs_count = Buff.query.filter(
                Buff.user_id == user.id,
                Buff.expires_at > time.time()
            ).count()
            
            # Add user data to list
            user_data = user.to_dict()
            user_data["active_buffs_count"] = active_buffs_count
            user_list.append(user_data)
        
        return jsonify({"users": user_list})
    except Exception as e:
        logger.error(f"Error fetching users: {e}")
        return jsonify({"error": str(e)}), 500

@dashboard_bp.route('/api/top_users')
def api_top_users():
    """API endpoint for getting top users."""
    try:
        # Get top 10 users
        top_users = User.query.order_by(User.deliveries.desc()).limit(10).all()
        
        # Format results
        result = [
            {
                "username": user.username,
                "deliveries": user.deliveries,
                "money": user.money,
                "experience": user.experience
            }
            for user in top_users
        ]
        
        return jsonify({"top_users": result})
    except Exception as e:
        logger.error(f"Error fetching top users: {e}")
        return jsonify({"error": str(e)}), 500

@dashboard_bp.route('/api/shop_items')
def api_shop_items():
    """API endpoint for getting shop items."""
    try:
        # Get all active shop items
        items = ShopItem.query.filter_by(is_active=True).all()
        
        # Format results
        result = [item.to_dict() for item in items]
        
        return jsonify({"shop_items": result})
    except Exception as e:
        logger.error(f"Error fetching shop items: {e}")
        return jsonify({"error": str(e)}), 500
