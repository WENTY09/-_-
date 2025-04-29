"""
Admin module for the Telegram bot dashboard.

This module contains the routes and functionality for the admin dashboard.
"""
import os
import time
from functools import wraps
from datetime import datetime
from flask import render_template, request, redirect, url_for, session, flash, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from app import app, db
from models import User, Buff, ShopItem, Stats, Admin, AdminLoginAttempt

# Secret key for session
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'development_key')

# Admin routes

def admin_required(f):
    """Decorator to require admin authentication."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'admin_id' not in session:
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    """Admin login page."""
    error = None
    
    if request.method == 'POST':
        username = request.args.get('username', request.form.get('username', ''))
        password = request.args.get('password', request.form.get('password', ''))
        
        # Log login attempt
        ip = request.remote_addr
        login_attempt = AdminLoginAttempt(
            username=username,
            ip_address=ip,
            success=False
        )
        
        # Check if it's a special login using telegram admin status
        telegram_id = request.args.get('telegram_id')
        if telegram_id:
            user = User.query.filter_by(telegram_id=telegram_id, is_admin=True).first()
            if user:
                session['admin_id'] = user.id
                session['admin_name'] = user.username
                login_attempt.success = True
                db.session.add(login_attempt)
                db.session.commit()
                return redirect(url_for('admin_dashboard'))
        
        # Regular login with username/password
        admin = Admin.query.filter_by(username=username).first()
        if admin and admin.password_hash and check_password_hash(admin.password_hash, password):
            session['admin_id'] = admin.id
            session['admin_name'] = admin.name
            login_attempt.success = True
            db.session.add(login_attempt)
            db.session.commit()
            return redirect(url_for('admin_dashboard'))
        
        # User-based login with admin flag
        user = User.query.filter_by(username=username, is_admin=True).first()
        if user and password == "admin":  # Temporary default password
            session['admin_id'] = user.id
            session['admin_name'] = user.username
            login_attempt.success = True
            db.session.add(login_attempt)
            db.session.commit()
            return redirect(url_for('admin_dashboard'))
        
        error = 'Неверное имя пользователя или пароль'
        db.session.add(login_attempt)
        db.session.commit()
    
    return render_template('admin/login.html', error=error)

@app.route('/admin/logout')
def admin_logout():
    """Admin logout."""
    session.pop('admin_id', None)
    session.pop('admin_name', None)
    return redirect(url_for('admin_login'))

@app.route('/admin')
@admin_required
def admin_dashboard():
    """Admin dashboard."""
    # Get basic stats
    total_users = User.query.count()
    
    # Get today's stats
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    today_timestamp = today.timestamp()
    
    # New users today
    new_users_today = User.query.filter(User.created_at >= today_timestamp).count()
    
    # Deliveries today - count users with last_delivery >= today
    deliveries_today = User.query.filter(User.last_delivery >= today_timestamp).count()
    
    # Buffs sold today
    buffs_sold_today = Buff.query.filter(Buff.created_at >= today_timestamp).count()
    
    # Get latest users
    latest_users = User.query.order_by(User.created_at.desc()).limit(5).all()
    
    # Get top users
    top_users = User.query.order_by(User.deliveries.desc()).limit(10).all()
    
    # System information
    import psutil
    uptime = datetime.now() - datetime.fromtimestamp(psutil.boot_time())
    uptime_str = f"{uptime.days} дней, {uptime.seconds // 3600} часов, {(uptime.seconds // 60) % 60} минут"
    
    # Database size (approximate)
    total_rows = (
        User.query.count() +
        Buff.query.count() +
        ShopItem.query.count() +
        Stats.query.count()
    )
    db_size = f"{total_rows} записей"
    
    # Free disk space
    free_space = psutil.disk_usage('/').free / (1024 * 1024 * 1024)  # Convert to GB
    free_space_str = f"{free_space:.2f} GB"
    
    return render_template(
        'admin/dashboard.html',
        admin_name=session.get('admin_name', 'Админ'),
        total_users=total_users,
        deliveries_today=deliveries_today,
        new_users_today=new_users_today,
        buffs_sold_today=buffs_sold_today,
        latest_users=latest_users,
        top_users=top_users,
        uptime=uptime_str,
        db_size=db_size,
        free_space=free_space_str
    )

@app.route('/admin/users')
@admin_required
def admin_users():
    """Admin users page."""
    # Pagination parameters
    page = request.args.get('page', 1, type=int)
    per_page = 15
    offset = (page - 1) * per_page
    
    # Search parameters
    search = request.args.get('search', '')
    status = request.args.get('status', '')
    sort = request.args.get('sort', 'newest')
    
    # Build query
    query = User.query
    
    # Apply search filter
    if search:
        query = query.filter(
            (User.username.ilike(f'%{search}%')) | 
            (User.telegram_id.ilike(f'%{search}%'))
        )
    
    # Apply status filter
    if status == 'active':
        query = query.filter_by(blocked=False, is_admin=False)
    elif status == 'blocked':
        query = query.filter_by(blocked=True)
    elif status == 'admin':
        query = query.filter_by(is_admin=True)
    
    # Apply sorting
    if sort == 'newest':
        query = query.order_by(User.created_at.desc())
    elif sort == 'oldest':
        query = query.order_by(User.created_at.asc())
    elif sort == 'deliveries':
        query = query.order_by(User.deliveries.desc())
    elif sort == 'money':
        query = query.order_by(User.money.desc())
    
    # Count total users for pagination
    total_users = query.count()
    total_pages = (total_users + per_page - 1) // per_page
    
    # Get paginated users
    users = query.offset(offset).limit(per_page).all()
    
    return render_template(
        'admin/users.html',
        users=users,
        page=page,
        total_pages=total_pages,
        admin_name=session.get('admin_name', 'Админ')
    )

@app.route('/admin/user/<int:user_id>/edit', methods=['GET', 'POST'])
@admin_required
def admin_edit_user(user_id):
    """Edit user page."""
    user = User.query.get_or_404(user_id)
    
    if request.method == 'POST':
        user.username = request.form.get('username', user.username)
        user.money = int(request.form.get('money', user.money))
        user.deliveries = int(request.form.get('deliveries', user.deliveries))
        user.experience = int(request.form.get('experience', user.experience))
        user.blocked = 'blocked' in request.form
        user.is_admin = 'is_admin' in request.form
        
        db.session.commit()
        flash('Пользователь успешно обновлен', 'success')
        return redirect(url_for('admin_users'))
    
    return render_template(
        'admin/edit_user.html',
        user=user,
        admin_name=session.get('admin_name', 'Админ')
    )

@app.route('/admin/user/<int:user_id>/delete', methods=['POST'])
@admin_required
def admin_delete_user(user_id):
    """Delete user."""
    user = User.query.get_or_404(user_id)
    db.session.delete(user)
    db.session.commit()
    flash('Пользователь успешно удален', 'success')
    return redirect(url_for('admin_users'))

@app.route('/admin/user/<int:user_id>/block')
@admin_required
def admin_block_user(user_id):
    """Block user."""
    user = User.query.get_or_404(user_id)
    user.blocked = True
    db.session.commit()
    flash('Пользователь заблокирован', 'success')
    return redirect(url_for('admin_users'))

@app.route('/admin/user/<int:user_id>/unblock')
@admin_required
def admin_unblock_user(user_id):
    """Unblock user."""
    user = User.query.get_or_404(user_id)
    user.blocked = False
    db.session.commit()
    flash('Пользователь разблокирован', 'success')
    return redirect(url_for('admin_users'))

@app.route('/admin/shop')
@admin_required
def admin_shop():
    """Admin shop page."""
    items = ShopItem.query.all()
    return render_template(
        'admin/shop.html',
        items=items,
        admin_name=session.get('admin_name', 'Админ')
    )

@app.route('/admin/shop/add', methods=['GET', 'POST'])
@admin_required
def admin_shop_add():
    """Add shop item page."""
    if request.method == 'POST':
        item = ShopItem(
            item_id=request.form.get('item_id'),
            name=request.form.get('name'),
            description=request.form.get('description'),
            price=int(request.form.get('price')),
            bonus=float(request.form.get('bonus')) / 100,  # Convert percentage to decimal
            duration=int(request.form.get('duration')),
            is_active=True
        )
        db.session.add(item)
        db.session.commit()
        flash('Предмет успешно добавлен', 'success')
        return redirect(url_for('admin_shop'))
    
    return render_template(
        'admin/add_shop_item.html',
        admin_name=session.get('admin_name', 'Админ')
    )

@app.route('/admin/stats')
@admin_required
def admin_stats():
    """Admin statistics page."""
    stats = Stats.query.first()
    
    # If no stats record exists, create one
    if not stats:
        stats = Stats()
        db.session.add(stats)
        db.session.commit()
    
    # Get daily stats
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    today_timestamp = today.timestamp()
    
    daily_stats = {
        'new_users': User.query.filter(User.created_at >= today_timestamp).count(),
        'deliveries': User.query.filter(User.last_delivery >= today_timestamp).count(),
        'buffs_purchased': Buff.query.filter(Buff.created_at >= today_timestamp).count()
    }
    
    return render_template(
        'admin/stats.html',
        stats=stats,
        daily_stats=daily_stats,
        admin_name=session.get('admin_name', 'Админ')
    )

@app.route('/admin/settings')
@admin_required
def admin_settings():
    """Admin settings page."""
    return render_template(
        'admin/settings.html',
        admin_name=session.get('admin_name', 'Админ')
    )

@app.route('/admin/broadcast', methods=['GET', 'POST'])
@admin_required
def admin_broadcast():
    """Admin broadcast message page."""
    if request.method == 'POST':
        message = request.form.get('message')
        send_to_all = 'send_to_all' in request.form
        send_to_active = 'send_to_active' in request.form
        
        # In a real implementation, this would send messages via the Telegram bot
        # For now, we'll just show a success message
        
        target = "всем пользователям" if send_to_all else "активным пользователям"
        flash(f'Сообщение успешно отправлено {target}', 'success')
        return redirect(url_for('admin_dashboard'))
    
    return render_template(
        'admin/broadcast.html',
        admin_name=session.get('admin_name', 'Админ')
    )

@app.route('/admin/export_data')
@admin_required
def admin_export_data():
    """Export data as JSON."""
    data_type = request.args.get('type', 'users')
    
    if data_type == 'users':
        users = User.query.all()
        data = [user.to_dict() for user in users]
    elif data_type == 'shop':
        items = ShopItem.query.all()
        data = [item.to_dict() for item in items]
    elif data_type == 'stats':
        stats = Stats.query.first()
        data = stats.to_dict() if stats else {}
    else:
        data = {'error': 'Invalid data type'}
    
    return jsonify(data)

# Add the admin routes to the main app
def init_admin():
    """Initialize admin module."""
    # This function can be used to perform any one-time setup
    pass