"""
Routes for the dashboard app.
"""
import os
import json
import time
import psutil
from flask import Blueprint, render_template, jsonify
from models import db, User, Buff, Admin

dashboard_bp = Blueprint('dashboard', __name__, url_prefix='')

@dashboard_bp.route('/')
def index():
    """Render the main dashboard page."""
    return render_template('index.html')

@dashboard_bp.route('/stats')
def stats_page():
    """Render the detailed statistics page."""
    return render_template('stats.html')

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
        
        # Format results
        stats = {
            "system": {
                "cpu": cpu_percent,
                "memory": memory_percent,
                "disk": disk_percent,
                "uptime": int(time.time() - psutil.boot_time())
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
        return jsonify({"error": str(e)}), 500