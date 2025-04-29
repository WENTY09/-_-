"""
Telegram bot command handlers.
"""
import logging
import random
import time
import os
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional, Any
import telebot
from telebot import types
from app import app
from models import User, Buff, ShopItem, db

# Set up logging
logger = logging.getLogger(__name__)

# Cache for shop item positions per user
shop_positions = {}

def register_handlers(bot):
    """
    Registers all handlers for bot commands.

    Args:
        bot: The TeleBot instance
    """
    # Command handlers with explicit bot parameter
    bot.register_message_handler(lambda msg: start_command(msg, bot), commands=['start'])
    bot.register_message_handler(lambda msg: raznos_command(msg, bot), commands=['raznos'])
    bot.register_message_handler(lambda msg: top_command(msg, bot), commands=['top'])
    bot.register_message_handler(lambda msg: profile_command(msg, bot), commands=['profile'])
    bot.register_message_handler(lambda msg: shop_command(msg, bot), commands=['magaz'])
    bot.register_message_handler(lambda msg: admin_command(msg, bot), commands=['adm'])

    # Handle text messages with menu buttons
    bot.register_message_handler(lambda msg: handle_text_button(msg, bot), content_types=['text'])

    # Callback query handlers
    @bot.callback_query_handler(func=lambda call: call.data.startswith('change_name'))
    def change_name_callback(call):
        """Handle the change_name callback."""
        bot.answer_callback_query(call.id)
        bot.delete_message(call.message.chat.id, call.message.message_id)
        msg = bot.send_message(call.message.chat.id, 
                              "Введите ваше новое имя курьера (до 20 символов):")
        bot.register_next_step_handler(msg, lambda m: process_name_change(m, bot))

    @bot.callback_query_handler(func=lambda call: call.data.startswith('shop_'))
    def shop_callback(call):
        """Handle shop navigation and purchase callbacks."""
        bot.answer_callback_query(call.id)

        parts = call.data.split('_')
        action = parts[1]
        user_id = call.from_user.id

        if action == 'prev' or action == 'next':
            current_index = int(parts[2]) if len(parts) > 2 else 0
            new_index = current_index - 1 if action == 'prev' else current_index + 1
            show_shop_item(call.message.chat.id, user_id, new_index, call.message.message_id, bot)

        elif action == 'buy':
            item_index = int(parts[2]) if len(parts) > 2 else 0
            success, message = purchase_buff(user_id, item_index)

            if success:
                bot.edit_message_text(
                    f"✅ {message}",
                    call.message.chat.id,
                    call.message.message_id,
                    parse_mode='HTML'
                )
                # Show user profile after purchase
                time.sleep(2)
                profile_command_internal(call.message, bot)
            else:
                bot.edit_message_text(
                    f"❌ {message}\n\nПопробуйте снова или выберите другой бафф.",
                    call.message.chat.id,
                    call.message.message_id,
                    parse_mode='HTML',
                    reply_markup=get_shop_nav_keyboard(item_index)
                )

def process_name_change(message, bot):
    """Process the name change request."""
    new_name = message.text.strip()

    if len(new_name) > 20:
        bot.reply_to(message, "❌ Имя слишком длинное! Максимальная длина - 20 символов.")
        return

    # Update user data with new name
    with app.app_context():
        user = get_or_create_user(message.from_user.id)
        user.username = new_name
        db.session.commit()

    bot.reply_to(message, f"✅ Имя курьера изменено на: {new_name}")

    # Show updated profile
    profile_command_internal(message, bot)

def start_command(message, bot):
    """Handle the /start command."""
    user_id = message.from_user.id

    with app.app_context():
        # Get or create user
        user = get_or_create_user(user_id)

        # Check if user is new
        is_new = user.deliveries == 0

        # Create main menu keyboard with web app button
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        repl_url = f'https://{os.getenv("REPL_SLUG")}.{os.getenv("REPL_OWNER")}.repl.co'
        webapp_btn = types.KeyboardButton(
            text='📱 Открыть приложение',
            web_app=types.WebAppInfo(url=repl_url)
        )
        markup.add(webapp_btn)
        
        # Add other buttons
        markup.add(
            types.KeyboardButton("Разносить посылки"),
            types.KeyboardButton("Мой профиль")
        )
        markup.add(
            types.KeyboardButton("Лучшие курьеры"),
            types.KeyboardButton("Магазин")
        )
            types.KeyboardButton("Разносить посылки"),
            types.KeyboardButton("Мой профиль")
        )
        markup.add(
            types.KeyboardButton("Лучшие курьеры"),
            types.KeyboardButton("Магазин")
        )

        if is_new:
            # Welcome message for new users
            bot.send_message(
                message.chat.id,
                f"👋 Привет, {message.from_user.first_name}!\n\n"
                f"Добро пожаловать в симулятор доставки! Я - бот, который поможет тебе стать "
                f"лучшим курьером.\n\n"
                f"📱 <b>Что умеет этот бот:</b>\n"
                f"• Симуляция работы курьера\n"
                f"• Разнос посылок с наградами\n"
                f"• Прокачка персонажа\n"
                f"• Покупка баффов на заработок\n"
                f"• Таблица лидеров\n\n"
                f"Начни доставлять посылки прямо сейчас с помощью команды <b>Разносить посылки</b>!",
                parse_mode='HTML',
                reply_markup=markup
            )
        else:
            # Welcome back message for existing users
            bot.send_message(
                message.chat.id,
                f"👋 С возвращением, {user.username}!\n\n"
                f"💰 У тебя {user.money} рублей\n"
                f"📦 Ты выполнил {user.deliveries} доставок\n\n"
                f"Используй кнопки меню для навигации:",
                parse_mode='HTML',
                reply_markup=markup
            )

def raznos_command(message, bot):
    """Handle the /raznos command."""
    user_id = message.from_user.id

    # Check if user can make a delivery (2-minute cooldown)
    can_do, time_remaining = can_deliver(user_id)

    if not can_do:
        if time_remaining:  # Check if remaining is not None
            minutes, seconds = divmod(time_remaining.seconds, 60)
            bot.reply_to(
                message,
                f"⏱ Вы недавно доставляли посылку! Следующая доставка будет доступна через "
                f"{minutes} мин. {seconds} сек."
            )
        else:
            bot.reply_to(
                message,
                f"⛔ Вы заблокированы и не можете делать доставки."
            )
        return

    # Generate random delivery earnings (100-300)
    earnings = random.randint(100, 300)
    deliveries = 1

    # Update user data (+1 delivery, +earnings money)
    original_earnings, buffed_earnings = update_user_data(user_id, deliveries, earnings)

    with app.app_context():
        user = get_or_create_user(user_id)

        # Prepare caption for the delivery image
        caption = (
            f"🚚 Доставка завершена!\n\n"
            f"💰 Заработано: {buffed_earnings} руб.\n"
            f"📦 Всего доставлено: {user.deliveries} шт.\n\n"
        )

        # Add buff message if there was a bonus
        if buffed_earnings > original_earnings:
            caption += f"🔮 Бонус от баффов: +{buffed_earnings - original_earnings} руб.\n\n"

        caption += f"💵 Баланс: {user.money} руб.\n"

        # Send delivery message
        bot.send_message(
            message.chat.id,
            caption,
            parse_mode='HTML'
        )

def top_command(message, bot):
    """Handle the /top command."""
    with app.app_context():
        # Get top 5 users
        top_users = User.query.order_by(User.deliveries.desc()).limit(5).all()

        # Build leaderboard message
        leaderboard = "🏆 Лучшие курьеры 📦\n\n"

        medals = ["🥇", "🥈", "🥉"]

        for i, user in enumerate(top_users):
            if i < 3:
                # Top 3 get medal emojis
                leaderboard += f"{medals[i]} {user.username} - {user.deliveries} доставок\n"
            else:
                # Rest get numerical position
                leaderboard += f"{i + 1}. {user.username} - {user.deliveries} доставок\n"

        # If there are fewer than 5 users, the message will be shorter
        if not top_users:
            leaderboard += "🤷‍♂️ Пока нет данных о курьерах! 🤷‍♀️"

        bot.send_message(
            message.chat.id,
            leaderboard,
            parse_mode='HTML'
        )

def profile_command(message, bot):
    """Handle the /profile command."""
    profile_command_internal(message, bot)

def profile_command_internal(message, bot):
    """Internal implementation of profile command to be reused."""
    user_id = message.from_user.id

    with app.app_context():
        user = get_or_create_user(user_id)

        # Get active buffs
        active_buffs = get_active_buffs(user_id)

        # Build active buffs message
        buffs_message = ""
        if active_buffs:
            buffs_message = "\n\n🔮 Активные баффы:\n"
            for buff in active_buffs:
                remaining_seconds = max(0, int(buff.expires_at - time.time()))
                minutes, seconds = divmod(remaining_seconds, 60)
                buffs_message += f"• {buff.name} (+{int(buff.bonus * 100)}%) - {minutes}м {seconds}с\n"

        # Build profile message
        profile_message = (
            f"👤 <b>Профиль курьера</b>\n\n"
            f"📛 Имя: <b>{user.username}</b>\n"
            f"📦 Доставлено: <b>{user.deliveries}</b> шт.\n"
            f"💵 Баланс: <b>{user.money}</b> руб."
            f"{buffs_message}"
        )

        # Create inline keyboard for changing name
        keyboard = types.InlineKeyboardMarkup()
        change_name_button = types.InlineKeyboardButton(text="✏️ Изменить имя", callback_data="change_name")
        keyboard.add(change_name_button)

        bot.send_message(
            message.chat.id,
            profile_message,
            parse_mode='HTML',
            reply_markup=keyboard
        )

def shop_command(message, bot):
    """Handle the /magaz command to open the shop."""
    user_id = message.from_user.id

    # Display the first shop item
    show_shop_item(message.chat.id, user_id, 0, None, bot)

def show_shop_item(chat_id, user_id, item_index, message_id, bot):
    """Display a shop item with navigation buttons."""
    with app.app_context():
        # Get all active shop items
        items = ShopItem.query.filter_by(is_active=True).all()

        # If no items, use default items
        if not items:
            # Initialize shop items if needed
            init_default_shop_items()
            items = ShopItem.query.filter_by(is_active=True).all()

        # Make sure index is within bounds
        item_count = len(items)
        if item_count == 0:
            bot.send_message(chat_id, "❌ Магазин временно пуст.")
            return

        # Ensure index is within bounds using modulo
        item_index = item_index % item_count
        item = items[item_index]

        # Get user's money
        user = get_or_create_user(user_id)

        # Create navigation keyboard
        keyboard = get_shop_nav_keyboard(item_index)

        # Format the message
        shop_message = (
            f"🏪 <b>{item.name}</b>\n\n"
            f"📝 {item.description}\n"
            f"⏱️ Длительность: <b>{item.duration} мин.</b>\n"
            f"💹 Бонус: <b>+{int(item.bonus * 100)}%</b>\n\n"
            f"💰 Цена: <b>{item.price} руб.</b>\n"
            f"💵 Ваш баланс: <b>{user.money} руб.</b>\n\n"
            f"<i>Предмет {item_index + 1} из {item_count}</i>"
        )

        # Edit or send new message
        if message_id:
            try:
                bot.edit_message_text(
                    shop_message,
                    chat_id=chat_id,
                    message_id=message_id,
                    parse_mode='HTML',
                    reply_markup=keyboard
                )
            except Exception as e:
                logger.error(f"Error editing shop message: {e}")
                # Try sending a new message instead
                bot.send_message(
                    chat_id,
                    shop_message,
                    parse_mode='HTML',
                    reply_markup=keyboard
                )
        else:
            bot.send_message(
                chat_id,
                shop_message,
                parse_mode='HTML',
                reply_markup=keyboard
            )

def get_shop_nav_keyboard(item_index):
    """Get inline keyboard for shop navigation."""
    keyboard = types.InlineKeyboardMarkup(row_width=3)
    prev_button = types.InlineKeyboardButton(text="⬅️", callback_data=f"shop_prev_{item_index}")
    buy_button = types.InlineKeyboardButton(text="🛒 Купить", callback_data=f"shop_buy_{item_index}")
    next_button = types.InlineKeyboardButton(text="➡️", callback_data=f"shop_next_{item_index}")
    keyboard.add(prev_button, buy_button, next_button)
    return keyboard

def admin_command(message, bot):
    """Handle the /adm command for admin panel."""
    user_id = message.from_user.id

    with app.app_context():
        # Check if user is admin
        user = get_or_create_user(user_id)

        if not user.is_admin:
            bot.send_message(
                message.chat.id,
                "⛔ У вас нет доступа к админ-панели."
            )
            return

        # Generate admin panel login URL with Telegram ID
        # Use a publicly accessible URL for Telegram
        admin_url = f"https://b0e0ddba-efbe-4725-b28c-b4ce6df495ab-00-3r0lzlw8pcxlb.janeway.replit.dev/admin/login?telegram_id={user.telegram_id}"

        # Create inline keyboard with login button
        keyboard = types.InlineKeyboardMarkup()
        url_button = types.InlineKeyboardButton(
            text="🔐 Войти в админ-панель", 
            url=admin_url
        )
        keyboard.add(url_button)

        bot.send_message(
            message.chat.id,
            "🛡️ <b>Админ-панель</b>\n\n"
            "Нажмите на кнопку ниже, чтобы войти в админ-панель.",
            parse_mode='HTML',
            reply_markup=keyboard
        )

def handle_text_button(message, bot):
    """Handle text messages from the keyboard."""
    text = message.text.lower()

    if text == "разносить посылки":
        raznos_command(message, bot)
    elif text == "мой профиль":
        profile_command(message, bot)
    elif text == "лучшие курьеры":
        top_command(message, bot)
    elif text == "магазин":
        shop_command(message, bot)

def create_main_menu_markup():
    """Create the main menu keyboard markup."""
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    item1 = types.KeyboardButton("Разносить посылки")
    item2 = types.KeyboardButton("Мой профиль")
    item3 = types.KeyboardButton("Лучшие курьеры")
    item4 = types.KeyboardButton("Магазин")
    markup.add(item1, item2, item3, item4)
    return markup

# Helper functions for database operations

def get_or_create_user(telegram_id):
    """Get or create a user record."""
    # Convert to string for consistent handling
    str_telegram_id = str(telegram_id)

    # Try to find existing user
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
            blocked=False
        )
        db.session.add(user)
        db.session.commit()

    return user

def can_deliver(telegram_id):
    """Check if a user can make a delivery (2-minute cooldown)."""
    with app.app_context():
        try:
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

        except Exception as e:
            logger.error(f"Error checking delivery cooldown: {e}")
            return True, None

def update_user_data(telegram_id, deliveries, earnings):
    """
    Update user data after a delivery.

    Returns:
        Tuple of (original_earnings, buffed_earnings)
    """
    with app.app_context():
        try:
            # Get user data
            user = get_or_create_user(telegram_id)

            # Calculate earnings with active buffs
            multiplier = get_active_earnings_multiplier(telegram_id)
            original_earnings = earnings
            buffed_earnings = int(earnings * (1 + multiplier))

            # Update user data
            user.deliveries += deliveries
            user.money += buffed_earnings
            user.experience += random.randint(1, 3)  # Random experience
            user.last_delivery = time.time()

            # Save to database
            db.session.commit()

            return original_earnings, buffed_earnings

        except Exception as e:
            logger.error(f"Error updating user data: {e}")
            db.session.rollback()
            return earnings, earnings

def get_active_earnings_multiplier(telegram_id):
    """
    Calculate the total earnings multiplier from all active buffs.

    Returns:
        Float multiplier (e.g., 0.25 for 25% increase)
    """
    with app.app_context():
        try:
            # Get user
            user = get_or_create_user(telegram_id)

            # Get active buffs
            now = time.time()
            active_buffs = Buff.query.filter(
                Buff.user_id == user.id,
                Buff.expires_at > now
            ).all()

            # Calculate total multiplier
            total_multiplier = sum(buff.bonus for buff in active_buffs)

            return total_multiplier

        except Exception as e:
            logger.error(f"Error calculating active earnings multiplier: {e}")
            return 0.0

def get_active_buffs(telegram_id):
    """Get active buffs for a user."""
    with app.app_context():
        user = get_or_create_user(telegram_id)
        now = time.time()

        return Buff.query.filter(
            Buff.user_id == user.id,
            Buff.expires_at > now
        ).all()

def purchase_buff(telegram_id, item_index):
    """
    Attempt to purchase a buff for the user.

    Returns:
        Tuple of (success, message)
    """
    with app.app_context():
        try:
            # Get user
            user = get_or_create_user(telegram_id)

            # Get all shop items
            items = ShopItem.query.filter_by(is_active=True).all()

            # Initialize shop items if needed
            if not items:
                init_default_shop_items()
                items = ShopItem.query.filter_by(is_active=True).all()

            # Check if items exist
            if not items:
                return False, "❌ Магазин временно пуст."

            # Get the selected item
            item_index = item_index % len(items)
            item = items[item_index]

            # Check if user has enough money
            if user.money < item.price:
                return False, f"❌ Недостаточно средств! Нужно: {item.price} рублей."

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

            return True, f"✅ Вы приобрели {item.name} на {item.duration} минут!"

        except Exception as e:
            logger.error(f"Error purchasing buff: {e}")
            db.session.rollback()
            return False, "❌ Произошла ошибка при покупке. Попробуйте позже."

def init_default_shop_items():
    """Initialize default shop items if none exist."""
    with app.app_context():
        # Check if items already exist
        if ShopItem.query.count() > 0:
            return

        # Default items
        items = [
            {
                "item_id": "hyper_buff",
                "name": "Гипер Бафф",
                "description": "Повышает доход на 50%",
                "price": 2750,
                "bonus": 0.5,
                "duration": 40
            },
            {
                "item_id": "super_buff",
                "name": "Супер Бафф",
                "description": "Повышает доход на 15%",
                "price": 850,
                "bonus": 0.15,
                "duration": 30
            },
            {
                "item_id": "mega_buff",
                "name": "Мега Бафф",
                "description": "Повышает доход на 25%",
                "price": 1800,
                "bonus": 0.25,
                "duration": 30
            }
        ]

        # Add items to database
        for item_data in items:
            item = ShopItem(**item_data, is_active=True)
            db.session.add(item)

        db.session.commit()
        logger.info("Default shop items initialized")