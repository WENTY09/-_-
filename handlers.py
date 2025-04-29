"""
Telegram Bot Command Handlers

This module contains all the handlers for bot commands and callback queries.
"""
import random
import logging
import os
from telebot import types
from datetime import datetime, timedelta
from user_data import (
    get_user_data, update_user_data, can_deliver, get_top_users,
    get_shop_item, purchase_buff, get_active_buffs_info, get_all_shop_items,
    get_shop_items_count
)
from delivery_image import create_delivery_image

# Configure logging
logger = logging.getLogger(__name__)

# Store the bot instance for use in command handlers
_bot = None

# Keep track of users' current shop position
shop_positions = {}

def register_handlers(bot):
    """
    Registers all handlers for bot commands.
    
    Args:
        bot: The TeleBot instance
    """
    global _bot
    _bot = bot
    
    # Register message handlers
    bot.message_handler(commands=['start'])(start_command)
    bot.message_handler(commands=['raznos'])(raznos_command)
    bot.message_handler(commands=['top'])(top_command)
    bot.message_handler(commands=['profile'])(profile_command)
    bot.message_handler(commands=['magaz'])(shop_command)
    
    # Handler for inline button callbacks
    @bot.callback_query_handler(func=lambda call: call.data == "change_name")
    def change_name_callback(call):
        # Answer the callback query to stop the loading animation
        bot.answer_callback_query(call.id)
        
        # Send message asking for a new name
        msg = bot.send_message(
            call.message.chat.id,
            "✏️ Введите новое имя для вашего профиля:",
            reply_markup=types.ForceReply(selective=True)
        )
        # Register the next step handler
        bot.register_next_step_handler(msg, process_name_change)
    
    # Shop navigation callbacks
    @bot.callback_query_handler(func=lambda call: call.data.startswith("shop_"))
    def shop_callback(call):
        user_id = call.from_user.id
        chat_id = call.message.chat.id
        message_id = call.message.message_id
        
        # Answer the callback query to stop the loading animation
        bot.answer_callback_query(call.id)
        
        # Get current position or initialize
        current_pos = shop_positions.get(user_id, 0)
        
        if call.data == "shop_prev":
            # Move to previous item
            current_pos = (current_pos - 1) % get_shop_items_count()
        elif call.data == "shop_next":
            # Move to next item
            current_pos = (current_pos + 1) % get_shop_items_count()
        elif call.data == "shop_buy":
            # Attempt to buy the item
            success, message = purchase_buff(user_id, current_pos)
            bot.send_message(chat_id, message)
            
            # Re-display the shop with updated balance
            show_shop_item(chat_id, user_id, current_pos, message_id)
            return
        
        # Update position and display the item
        shop_positions[user_id] = current_pos
        show_shop_item(chat_id, user_id, current_pos, message_id)

def process_name_change(message):
    """Process the name change request."""
    user_id = message.from_user.id
    new_name = message.text.strip()
    
    # Validate name
    if not new_name or len(new_name) > 20:
        _bot.send_message(
            message.chat.id,
            "Имя должно быть от 1 до 20 символов. Попробуйте снова с командой /profile."
        )
        return
    
    # Update user data with new name
    user_data = get_user_data(user_id)
    user_data["username"] = new_name
    
    # Confirm the change
    _bot.send_message(
        message.chat.id,
        f"✅ Ваше имя изменено на *{new_name}*. Изменения отразятся в вашем профиле.",
        parse_mode="Markdown"
    )

def start_command(message):
    """Handle the /start command."""
    user_id = message.from_user.id
    first_name = message.from_user.first_name
    
    # Store username in user data
    data = get_user_data(user_id)
    data["username"] = first_name
    
    welcome_message = (
        f"👋 Привет *{first_name}* жми *команду /raznos* и разноси первые "
        f"посылки и получай деньги! 💰✨\n\n"
        f"📊 Смотри свой *прогресс в /profile*\n"
        f"🛒 Покупай *усиления в /magaz*"
    )
    
    _bot.send_message(
        message.chat.id,
        welcome_message,
        parse_mode="Markdown"
    )

def raznos_command(message):
    """Handle the /raznos command."""
    user_id = message.from_user.id
    
    # Check if user is in cooldown
    can_do_delivery, time_remaining = can_deliver(user_id)
    
    if not can_do_delivery and time_remaining:
        # User is in cooldown, inform them of the remaining time
        minutes = time_remaining.seconds // 60
        seconds = time_remaining.seconds % 60
        
        cooldown_message = (
            f"⏳ Ты уже недавно разносил подарки!\n"
            f"⌚ Следущий заказ через *{minutes}* мин. *{seconds}* сек. 🕒"
        )
        
        _bot.send_message(
            message.chat.id,
            cooldown_message,
            parse_mode="Markdown"
        )
        return
    
    # Generate random delivery data
    deliveries = random.randint(1, 3)
    base_earnings = random.randint(35, 200)
    
    # Update user data and get buffed earnings
    original_earnings, buffed_earnings = update_user_data(user_id, deliveries, base_earnings)
    user_data = get_user_data(user_id)
    
    # Get delivery image
    image_path = create_delivery_image()
    
    # Prepare response message with correct Russian grammar
    package_word = "посылку"
    if deliveries > 1 and deliveries < 5:
        package_word = "посылки"
    elif deliveries >= 5:
        package_word = "посылок"
    
    # Check if experience is at a multiple of 100, add bonus
    old_exp = user_data['experience'] - 1  # Experience before this delivery
    new_exp = user_data['experience']
    
    bonus_message = ""
    if old_exp // 100 < new_exp // 100:
        # User has reached a new 100-experience milestone
        bonus = random.randint(1, 100)
        user_data['money'] += bonus
        bonus_message = f"🎉 Бонус за {new_exp // 100 * 100} опыта: +{bonus} рублей!\n\n"
    
    # Add buff information if applicable
    buff_message = ""
    if buffed_earnings > original_earnings:
        buff_message = f"💎 Бонус от улучшений: +{buffed_earnings - original_earnings} рублей!\n\n"
    
    delivery_message = (
        f"🚚 Доставка завершена! 📬\n"
        f"👏 Ты разнес {deliveries} {package_word}\n\n"
        f"💸 Ты получил {buffed_earnings} рублей\n\n"
        f"{bonus_message}{buff_message}💪 Опыт разносчика - {user_data['experience']}/500 ✨"
    )
    
    # Send the image with caption
    with open(image_path, 'rb') as photo:
        _bot.send_photo(
            message.chat.id, 
            photo,
            caption=delivery_message
        )

def top_command(message):
    """Handle the /top command."""
    # Get top 5 users
    top_users = get_top_users(5)
    
    # Build leaderboard message
    leaderboard = "🏆 Лучшие разносчики 🎖\n\n"
    
    medals = ["🥇", "🥈", "🥉"]
    
    for i, (_, username, deliveries) in enumerate(top_users):
        if i < 3:
            # Top 3 get medal emojis
            leaderboard += f"{medals[i]} место *{username}* - *{deliveries}* доставок 📦\n"
        else:
            # Rest get numerical position
            leaderboard += f"{i + 1}. место *{username}* - *{deliveries}* доставок 📦\n"
    
    # If there are fewer than 5 users, the message will be shorter
    if not top_users:
        leaderboard += "🤷‍♂️ Пока нет данных о разносчиках! 🤷‍♀️"
    
    _bot.send_message(
        message.chat.id,
        leaderboard,
        parse_mode="Markdown"
    )
    
def profile_command(message):
    """Handle the /profile command."""
    user_id = message.from_user.id
    user_data = get_user_data(user_id)
    
    # Get username or default to the one from Telegram
    username = user_data.get("username", message.from_user.first_name)
    
    # Get active buffs info
    active_buffs = get_active_buffs_info(user_id)
    
    # Build active buffs message
    buffs_message = ""
    if active_buffs:
        buffs_message = "\n\n🔮 Активные улучшения:\n"
        for buff in active_buffs:
            buffs_message += f"• {buff['name']} (+{int(buff['multiplier'] * 100)}%) - {buff['remaining_minutes']}м {buff['remaining_seconds']}с\n"
    
    # Build profile message
    profile_message = (
        f"🌟 Профиль курьера *{username}* 🌟\n\n"
        f"📦 Коробок разнесено: *{user_data['deliveries']}* шт.\n"
        f"💡 Опыт разносчика: *{user_data['experience']}* ✨\n"
        f"💰 Баланс: *{user_data.get('money', 0)}* рублей 💵"
        f"{buffs_message}\n\n"
        f"🔄 Продолжай доставлять посылки командой /raznos 🚚\n"
        f"🛒 Покупай усиления в магазине /magaz 🏪"
    )
    
    # Create inline keyboard for changing name
    keyboard = types.InlineKeyboardMarkup()
    change_name_button = types.InlineKeyboardButton(text="✏️ Изменить имя", callback_data="change_name")
    keyboard.add(change_name_button)
    
    _bot.send_message(
        message.chat.id,
        profile_message,
        parse_mode="Markdown",
        reply_markup=keyboard
    )

def shop_command(message):
    """Handle the /magaz command to open the shop."""
    user_id = message.from_user.id
    
    # Start with first item
    shop_positions[user_id] = 0
    
    # Display the first shop item
    show_shop_item(message.chat.id, user_id, 0)

def show_shop_item(chat_id, user_id, item_index, message_id=None):
    """Display a shop item with navigation buttons."""
    # Get item details
    item = get_shop_item(item_index)
    user_data = get_user_data(user_id)
    
    # Create navigation keyboard
    keyboard = types.InlineKeyboardMarkup(row_width=3)
    prev_button = types.InlineKeyboardButton(text="⬅️", callback_data="shop_prev")
    buy_button = types.InlineKeyboardButton(text="🔥 Купить 🔥", callback_data="shop_buy")
    next_button = types.InlineKeyboardButton(text="➡️", callback_data="shop_next")
    keyboard.add(prev_button, buy_button, next_button)
    
    # Format the caption
    caption = (
        f"🏪 *{item['name']}* 🏪\n\n"
        f"📝 {item['description']}\n"
        f"⏱ Срок действия: {item['duration_minutes']} минут\n\n"
        f"💰 Цена: *{item['price']}* рублей\n"
        f"💵 Ваш баланс: *{user_data.get('money', 0)}* рублей\n\n"
        f"{item_index + 1}/{get_shop_items_count()}"
    )
    
    # Try to open the image
    image_path = create_delivery_image()
    
    # Check if we need to edit existing message or send new one
    try:
        if message_id:
            with open(image_path, 'rb') as photo:
                _bot.edit_message_media(
                    media=types.InputMediaPhoto(photo, caption=caption, parse_mode="Markdown"),
                    chat_id=chat_id,
                    message_id=message_id,
                    reply_markup=keyboard
                )
        else:
            with open(image_path, 'rb') as photo:
                _bot.send_photo(
                    chat_id,
                    photo,
                    caption=caption,
                    parse_mode="Markdown",
                    reply_markup=keyboard
                )
    except Exception as e:
        logger.error(f"Error showing shop item: {e}")
