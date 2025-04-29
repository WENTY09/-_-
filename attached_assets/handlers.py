"""
Telegram bot command handlers.
"""
import logging
import random
import time
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional, Any
import telebot
from telebot import types
from telegram_bot.user_data import (
    get_user_data, update_user_data, can_deliver, get_top_users,
    get_shop_item, purchase_buff, get_active_buffs_info,
    is_admin, is_admin_with_permission, get_admin_permissions,
    add_admin, remove_admin, update_admin_permissions,
    block_user, unblock_user, add_money, remove_money, give_buff,
    get_all_users, get_user_details, get_all_admins, prepare_broadcast,
    get_all_shop_items, add_shop_item, edit_shop_item, delete_shop_item,
    SHOP_ITEMS, ROLE_OWNER, ROLE_ADMIN
)
from telegram_bot.delivery_image import create_delivery_image

# Set up logging
logger = logging.getLogger(__name__)

def register_handlers(bot):
    """
    Registers all handlers for bot commands.
    
    Args:
        bot: The TeleBot instance
    """
    # Command handlers
    bot.register_message_handler(lambda msg: start_command(msg, bot), commands=['start'])
    bot.register_message_handler(lambda msg: raznos_command(msg, bot), commands=['raznos'])
    bot.register_message_handler(lambda msg: top_command(msg, bot), commands=['top'])
    bot.register_message_handler(lambda msg: profile_command(msg, bot), commands=['profile'])
    bot.register_message_handler(lambda msg: shop_command(msg, bot), commands=['magaz'])
    bot.register_message_handler(lambda msg: admin_command(msg, bot), commands=['admin'])
    
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
            current_index = int(parts[2])
            new_index = current_index - 1 if action == 'prev' else current_index + 1
            show_shop_item(call.message.chat.id, user_id, new_index, call.message.message_id, bot)
        
        elif action == 'buy':
            item_index = int(parts[2])
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
    
    @bot.callback_query_handler(func=lambda call: call.data.startswith('menu_'))
    def menu_callback(call):
        """Handle menu navigation callbacks."""
        bot.answer_callback_query(call.id)
        
        action = call.data.split('_')[1]
        
        if action == 'main':
            # Return to main menu
            start_command(call.message, bot)
        
    @bot.callback_query_handler(func=lambda call: call.data.startswith('admin_'))
    def admin_callback(call):
        """Handle admin panel callbacks."""
        bot.answer_callback_query(call.id)
        
        user_id = call.from_user.id
        chat_id = call.message.chat.id
        
        # Check if user is admin
        if not is_admin(user_id):
            bot.send_message(chat_id, "❌ У вас нет доступа к админ-панели.")
            return
        
        parts = call.data.split('_')
        action = parts[1]
        
        # Handle different admin actions
        if action == 'users':
            # Show user list
            show_user_list(chat_id, user_id, bot)
        
        elif action == 'block':
            # Show block user menu
            show_block_menu(chat_id, user_id, bot)
        
        elif action == 'money':
            # Show money management menu
            show_money_menu(chat_id, user_id, bot)
        
        elif action == 'give_buff':
            # Show give buff menu
            show_give_buff_menu(chat_id, user_id, bot)
        
        elif action == 'items':
            # Show shop items management menu
            show_shop_items_menu(chat_id, user_id, bot)
        
        elif action == 'broadcast':
            # Show broadcast menu
            show_broadcast_menu(chat_id, user_id, bot)
        
        elif action == 'admins':
            # Show admin management menu
            show_admin_management(chat_id, user_id, bot)
        
        # Handle user interaction for specific admin actions
        elif action == 'block_user':
            target_id = int(parts[2])
            success, message = block_user(user_id, target_id)
            bot.send_message(chat_id, f"{'✅' if success else '❌'} {message}")
            
        elif action == 'unblock_user':
            target_id = int(parts[2])
            success, message = unblock_user(user_id, target_id)
            bot.send_message(chat_id, f"{'✅' if success else '❌'} {message}")
            
        elif action == 'user_info':
            target_id = int(parts[2])
            show_user_info(chat_id, user_id, target_id, bot)
            
        elif action == 'add_item':
            # Start creating a new shop item
            msg = bot.send_message(chat_id, 
                                  "🛒 <b>Добавление нового товара</b>\n\n"
                                  "Введите данные в формате:\n"
                                  "<название> | <описание> | <цена> | <бонус в %> | <длительность в мин>\n\n"
                                  "Например:\n"
                                  "Гипер Бафф | Увеличивает доход на 50% | 5000 | 50 | 40",
                                  parse_mode='HTML')
            bot.register_next_step_handler(msg, lambda m: process_add_item(m, user_id, bot))
        
        elif action == 'edit_item':
            # Start editing a shop item
            msg = bot.send_message(chat_id,
                                  "🛒 <b>Редактирование товара</b>\n\n"
                                  "Введите данные в формате:\n"
                                  "<ID товара> | <название> | <описание> | <цена> | <бонус в %> | <длительность в мин>\n\n"
                                  "Любое поле, кроме ID, можно оставить пустым (|), чтобы не менять его.\n\n"
                                  "Например:\n"
                                  "1 | Супер Бафф | | 3000 | | 30",
                                  parse_mode='HTML')
            bot.register_next_step_handler(msg, lambda m: process_edit_item(m, user_id, bot))
        
        elif action == 'delete_item':
            # Start deleting a shop item
            msg = bot.send_message(chat_id,
                                  "🛒 <b>Удаление товара</b>\n\n"
                                  "Введите ID товара, который хотите удалить.\n\n"
                                  "Например: 2",
                                  parse_mode='HTML')
            bot.register_next_step_handler(msg, lambda m: process_delete_item(m, user_id, bot))
        
        elif action == 'back':
            # Return to admin menu
            show_admin_menu(chat_id, user_id, bot)

def process_name_change(message, bot):
    """Process the name change request."""
    new_name = message.text.strip()
    
    if len(new_name) > 20:
        bot.reply_to(message, "❌ Имя слишком длинное! Максимальная длина - 20 символов.")
        return
    
    # Update user data with new name
    user_data = get_user_data(message.from_user.id)
    user_data['username'] = new_name
    
    bot.reply_to(message, f"✅ Имя курьера изменено на: {new_name}")
    
    # Show updated profile
    profile_command_internal(message, bot)

def start_command(message, bot):
    """Handle the /start command."""
    user_id = message.from_user.id
    user_data = get_user_data(user_id)
    
    # Check if user is new
    is_new = user_data['deliveries'] == 0
    
    # Create main menu keyboard
    markup = create_main_menu_markup()
    
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
            f"👋 С возвращением, {user_data['username']}!\n\n"
            f"💰 У тебя {user_data['money']} рублей\n"
            f"📦 Ты выполнил {user_data['deliveries']} доставок\n\n"
            f"Используй кнопки меню для навигации:",
            parse_mode='HTML',
            reply_markup=markup
        )
    
    # Check if user is admin and show admin menu
    if is_admin(user_id):
        show_admin_menu(message.chat.id, user_id, bot)

def raznos_command(message, bot):
    """Handle the /raznos command."""
    user_id = message.from_user.id
    
    # Check if user can make a delivery (7-minute cooldown)
    can_do, remaining = can_deliver(user_id)
    
    if not can_do:
        if remaining:  # Check if remaining is not None
            minutes, seconds = divmod(remaining.seconds, 60)
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
    
    # Update user data (+1 delivery, +earnings money)
    original_earnings, buffed_earnings = update_user_data(user_id, 1, earnings)
    
    # Get buff multiplier if any
    buff_multiplier = buffed_earnings / original_earnings if original_earnings > 0 else 1
    
    # Generate and send delivery image
    delivery_image = create_delivery_image()
    
    # Send delivery completion message with image
    if buff_multiplier > 1:
        caption = (
            f"✅ Доставка завершена!\n\n"
            f"💰 Заработано: {original_earnings} руб. + {buffed_earnings - original_earnings} руб. (бонус)\n"
            f"💵 Итого: {buffed_earnings} руб.\n\n"
            f"📊 Активен множитель: x{buff_multiplier:.2f}"
        )
    else:
        caption = (
            f"✅ Доставка завершена!\n\n"
            f"💰 Заработано: {buffed_earnings} руб."
        )
    
    # Check if we have a delivery image, if not, just send the message
    if delivery_image:
        with open(delivery_image, 'rb') as photo:
            bot.send_photo(message.chat.id, photo, caption=caption)
    else:
        bot.send_message(message.chat.id, caption)

def top_command(message, bot):
    """Handle the /top command."""
    top_users = get_top_users(10)  # Get top 10 users
    
    if not top_users:
        bot.send_message(message.chat.id, "📊 Пока никто не совершил ни одной доставки!")
        return
    
    # Create message with top users
    msg = "🏆 <b>Топ курьеров:</b>\n\n"
    
    for i, (user_id, username, deliveries) in enumerate(top_users):
        # Add medal emoji for top 3
        if i == 0:
            medal = "🥇"
        elif i == 1:
            medal = "🥈"
        elif i == 2:
            medal = "🥉"
        else:
            medal = f"{i+1}."
        
        msg += f"{medal} <b>{username}</b> - {deliveries} доставок\n"
    
    bot.send_message(message.chat.id, msg, parse_mode='HTML')

def profile_command(message, bot):
    """Handle the /profile command."""
    profile_command_internal(message, bot)

def profile_command_internal(message, bot):
    """Internal implementation of profile command to be reused."""
    user_id = message.from_user.id
    user_data = get_user_data(user_id)
    
    # Get active buffs info
    active_buffs = get_active_buffs_info(user_id)
    buffs_text = ""
    
    if active_buffs:
        buffs_text = "\n\n🔮 <b>Активные баффы:</b>\n"
        for buff in active_buffs:
            buffs_text += f"• {buff['name']} - осталось {buff['remaining_time']}\n"
    
    # Create inline keyboard for changing name
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("✏️ Изменить имя", callback_data=f"change_name"))
    
    bot.send_message(
        message.chat.id,
        f"👤 <b>Профиль курьера</b>\n\n"
        f"📝 Имя: <b>{user_data['username']}</b>\n"
        f"📦 Доставок: <b>{user_data['deliveries']}</b>\n"
        f"💰 Баланс: <b>{user_data['money']} руб.</b>"
        f"{buffs_text}",
        parse_mode='HTML',
        reply_markup=markup
    )

def shop_command(message, bot):
    """Handle the /magaz command to open the shop."""
    show_shop_item(message.chat.id, message.from_user.id, 0, None, bot)

def admin_command(message, bot):
    """Handle the /admin command."""
    user_id = message.from_user.id
    
    # Check if user is admin
    if is_admin(user_id):
        show_admin_menu(message.chat.id, user_id, bot)
    else:
        bot.reply_to(message, "❌ У вас нет доступа к админ-панели.")

def handle_text_button(message, bot):
    """Handle text messages from the keyboard."""
    text = message.text
    
    if text == "📦 Разносить посылки":
        raznos_command(message, bot)
    elif text == "👤 Профиль":
        profile_command(message, bot)
    elif text == "🏆 Топ курьеров":
        top_command(message, bot)
    elif text == "🛒 Магазин":
        shop_command(message, bot)
    elif text == "ℹ️ Инфо":
        info_command(message, bot)

def info_command(message, bot):
    """Show bot information."""
    bot.send_message(
        message.chat.id,
        f"ℹ️ <b>Информация о боте</b>\n\n"
        f"Этот бот симулирует работу курьера по доставке посылок.\n\n"
        f"<b>Основные команды:</b>\n"
        f"📦 /raznos или 'Разносить посылки' - Доставка посылок\n"
        f"👤 /profile или 'Профиль' - Показать ваш профиль\n"
        f"🏆 /top или 'Топ курьеров' - Таблица лидеров\n"
        f"🛒 /magaz или 'Магазин' - Магазин улучшений\n\n"
        f"<b>Особенности:</b>\n"
        f"• Кулдаун между доставками: 7 минут\n"
        f"• Оплата за доставку: 100-300 рублей\n"
        f"• Возможность покупать баффы для увеличения дохода\n"
        f"• Таблица лидеров с топ-10 курьеров\n\n"
        f"<b>Разработчик:</b> @white_wenty",
        parse_mode='HTML'
    )

def show_shop_item(chat_id, user_id, item_index, message_id, bot):
    """Display a shop item with navigation buttons."""
    item = get_shop_item(item_index)
    
    if not item:
        bot.send_message(chat_id, "❌ Товар не найден.")
        return
    
    # Get user data for showing current balance
    user_data = get_user_data(user_id)
    
    # Create shop item message
    msg = (
        f"🛒 <b>Магазин улучшений</b> [{item_index + 1}/3]\n\n"
        f"🔮 <b>{item['name']}</b>\n\n"
        f"📝 {item['description']}\n"
        f"⏱ Длительность: {item['duration']} минут\n"
        f"💰 Цена: {item['price']} руб.\n\n"
        f"💵 Ваш баланс: {user_data['money']} руб."
    )
    
    # Create navigation keyboard
    keyboard = get_shop_nav_keyboard(item_index)
    
    # Send or edit message
    if message_id:
        bot.edit_message_text(
            msg, chat_id, message_id,
            parse_mode='HTML', reply_markup=keyboard
        )
    else:
        bot.send_message(
            chat_id, msg,
            parse_mode='HTML', reply_markup=keyboard
        )

def get_shop_nav_keyboard(item_index):
    """Get inline keyboard for shop navigation."""
    keyboard = types.InlineKeyboardMarkup(row_width=3)
    
    # Previous button (disabled for first item)
    prev_button = types.InlineKeyboardButton(
        "◀️", callback_data=f"shop_prev_{item_index}"
    ) if item_index > 0 else types.InlineKeyboardButton(
        "🚫", callback_data=f"shop_none"
    )
    
    # Buy button
    buy_button = types.InlineKeyboardButton(
        "💰 Купить", callback_data=f"shop_buy_{item_index}"
    )
    
    # Next button (disabled for last item)
    next_button = types.InlineKeyboardButton(
        "▶️", callback_data=f"shop_next_{item_index}"
    ) if item_index < 2 else types.InlineKeyboardButton(
        "🚫", callback_data=f"shop_none"
    )
    
    keyboard.add(prev_button, buy_button, next_button)
    
    # Back to main menu button
    keyboard.add(types.InlineKeyboardButton("🏠 В главное меню", callback_data="menu_main"))
    
    return keyboard

# Main menu functions
def create_main_menu_markup():
    """Create the main menu keyboard markup."""
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    
    # Add buttons with emojis
    markup.add(
        types.KeyboardButton("📦 Разносить посылки")
    )
    markup.add(
        types.KeyboardButton("👤 Профиль"),
        types.KeyboardButton("🏆 Топ курьеров")
    )
    markup.add(
        types.KeyboardButton("🛒 Магазин"),
        types.KeyboardButton("ℹ️ Инфо")
    )
    
    return markup

# Admin panel functions
def show_admin_menu(chat_id, user_id, bot):
    """Show admin menu to user with admin rights."""
    permissions = get_admin_permissions(user_id)
    
    # Create admin menu with available options based on permissions
    markup = types.InlineKeyboardMarkup(row_width=2)
    
    if permissions.get("view_users", False):
        markup.add(types.InlineKeyboardButton("👥 Список пользователей", callback_data="admin_users"))
    
    if permissions.get("block_users", False):
        markup.add(types.InlineKeyboardButton("🚫 Блокировка пользователей", callback_data="admin_block"))
    
    if permissions.get("add_money", False) or permissions.get("remove_money", False):
        markup.add(types.InlineKeyboardButton("💰 Управление балансами", callback_data="admin_money"))
    
    if permissions.get("give_items", False):
        markup.add(types.InlineKeyboardButton("🎁 Выдать предмет", callback_data="admin_give_buff"))
    
    if permissions.get("manage_items", False):
        markup.add(types.InlineKeyboardButton("🛒 Управление товарами", callback_data="admin_items"))
    
    if permissions.get("broadcast", False):
        markup.add(types.InlineKeyboardButton("📣 Рассылка", callback_data="admin_broadcast"))
    
    if permissions.get("manage_admins", False):
        markup.add(types.InlineKeyboardButton("👑 Управление администраторами", callback_data="admin_admins"))
    
    # Send admin menu
    bot.send_message(
        chat_id,
        "🔐 <b>Панель администратора</b>\n\n"
        "Выберите действие из меню ниже:",
        parse_mode='HTML',
        reply_markup=markup
    )

# Admin panel implementation functions
def show_user_list(chat_id, admin_id, bot, page=0, page_size=5):
    """Show a paginated list of all users."""
    if not is_admin_with_permission(admin_id, "view_users"):
        bot.send_message(chat_id, "❌ У вас нет прав для просмотра пользователей.")
        return
    
    users = get_all_users()
    
    if not users:
        bot.send_message(chat_id, "❌ Пользователи не найдены.")
        return
    
    # Calculate pagination
    total_pages = (len(users) + page_size - 1) // page_size
    start_idx = page * page_size
    end_idx = min(start_idx + page_size, len(users))
    
    # Create message with user list
    msg = f"👥 <b>Список пользователей</b> (страница {page+1}/{total_pages}):\n\n"
    
    for i, user in enumerate(users[start_idx:end_idx], start=start_idx+1):
        status = "🔴 Заблокирован" if user.get("blocked", False) else "🟢 Активен"
        msg += (f"{i}. <b>{user['username']}</b> (ID: {user['user_id']})\n"
                f"   💰 {user['money']} руб. | 📦 {user['deliveries']} доставок\n"
                f"   Статус: {status}\n\n")
    
    # Create navigation keyboard
    keyboard = types.InlineKeyboardMarkup(row_width=3)
    
    # Previous button
    prev_button = types.InlineKeyboardButton(
        "◀️", callback_data=f"admin_users_page_{page-1}"
    ) if page > 0 else types.InlineKeyboardButton(
        "🚫", callback_data="admin_none"
    )
    
    # Home button
    home_button = types.InlineKeyboardButton("🏠", callback_data="admin_back")
    
    # Next button
    next_button = types.InlineKeyboardButton(
        "▶️", callback_data=f"admin_users_page_{page+1}"
    ) if page < total_pages - 1 else types.InlineKeyboardButton(
        "🚫", callback_data="admin_none"
    )
    
    keyboard.add(prev_button, home_button, next_button)
    
    # Add view user button
    keyboard.add(types.InlineKeyboardButton(
        "👁️ Просмотр информации о пользователе", callback_data="admin_view_user"
    ))
    
    bot.send_message(chat_id, msg, parse_mode='HTML', reply_markup=keyboard)

def show_user_info(chat_id, admin_id, user_id, bot):
    """Show detailed information about a user."""
    if not is_admin_with_permission(admin_id, "view_users"):
        bot.send_message(chat_id, "❌ У вас нет прав для просмотра информации о пользователях.")
        return
    
    user_details = get_user_details(user_id)
    
    if not user_details:
        bot.send_message(chat_id, "❌ Пользователь не найден.")
        return
    
    # Format active buffs
    buffs_text = ""
    if user_details["active_buffs"]:
        buffs_text = "\n\n🔮 <b>Активные баффы:</b>\n"
        for buff in user_details["active_buffs"]:
            buffs_text += f"• {buff['name']} - осталось {buff['remaining_time']}\n"
    
    # Create message with user details
    msg = (f"👤 <b>Информация о пользователе:</b>\n\n"
           f"ID: {user_details['user_id']}\n"
           f"Имя: <b>{user_details['username']}</b>\n"
           f"Доставок: <b>{user_details['deliveries']}</b>\n"
           f"Баланс: <b>{user_details['money']} руб.</b>\n"
           f"Статус: {'🔴 Заблокирован' if user_details['blocked'] else '🟢 Активен'}\n"
           f"Последняя доставка: {user_details['last_delivery_time']}"
           f"{buffs_text}")
    
    # Create action keyboard
    keyboard = types.InlineKeyboardMarkup(row_width=2)
    
    # Add block/unblock button
    if user_details["blocked"]:
        keyboard.add(types.InlineKeyboardButton(
            "🟢 Разблокировать", callback_data=f"admin_unblock_user_{user_id}"
        ))
    else:
        keyboard.add(types.InlineKeyboardButton(
            "🔴 Заблокировать", callback_data=f"admin_block_user_{user_id}"
        ))
    
    # Add money management buttons
    keyboard.add(
        types.InlineKeyboardButton("💰 Добавить деньги", callback_data=f"admin_add_money_{user_id}"),
        types.InlineKeyboardButton("💸 Удалить деньги", callback_data=f"admin_remove_money_{user_id}")
    )
    
    # Add give buff button
    keyboard.add(types.InlineKeyboardButton(
        "🎁 Выдать бафф", callback_data=f"admin_give_buff_{user_id}"
    ))
    
    # Add back button
    keyboard.add(types.InlineKeyboardButton("🔙 Назад", callback_data="admin_users"))
    
    bot.send_message(chat_id, msg, parse_mode='HTML', reply_markup=keyboard)

def show_block_menu(chat_id, admin_id, bot):
    """Show menu for blocking/unblocking users."""
    if not is_admin_with_permission(admin_id, "block_users"):
        bot.send_message(chat_id, "❌ У вас нет прав для блокировки пользователей.")
        return
    
    # Create message and keyboard
    msg = (f"🚫 <b>Блокировка пользователей</b>\n\n"
           f"Введите ID пользователя для блокировки/разблокировки.\n"
           f"Для блокировки введите: block <user_id>\n"
           f"Для разблокировки введите: unblock <user_id>\n\n"
           f"Например: block 123456789")
    
    # Create keyboard with back button
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(types.InlineKeyboardButton("🔙 Назад", callback_data="admin_back"))
    
    # Send message
    msg = bot.send_message(chat_id, msg, parse_mode='HTML', reply_markup=keyboard)
    
    # Register next step handler
    bot.register_next_step_handler(msg, lambda m: process_block_command(m, admin_id, bot))

def process_block_command(message, admin_id, bot):
    """Process block/unblock command."""
    text = message.text.strip().split()
    
    if len(text) != 2:
        bot.send_message(message.chat.id, "❌ Неверный формат команды. Пример: block 123456789")
        return
    
    command, user_id_str = text
    
    try:
        user_id = int(user_id_str)
    except ValueError:
        bot.send_message(message.chat.id, "❌ ID пользователя должен быть числом.")
        return
    
    if command.lower() == "block":
        success, message_text = block_user(admin_id, user_id)
    elif command.lower() == "unblock":
        success, message_text = unblock_user(admin_id, user_id)
    else:
        bot.send_message(message.chat.id, "❌ Неизвестная команда. Используйте block или unblock.")
        return
    
    bot.send_message(message.chat.id, f"{'✅' if success else '❌'} {message_text}")

def show_money_menu(chat_id, admin_id, bot):
    """Show menu for adding/removing money."""
    if not (is_admin_with_permission(admin_id, "add_money") or
            is_admin_with_permission(admin_id, "remove_money")):
        bot.send_message(chat_id, "❌ У вас нет прав для управления балансами.")
        return
    
    # Create message and keyboard
    msg = (f"💰 <b>Управление балансами</b>\n\n"
           f"Введите ID пользователя и сумму для изменения баланса.\n"
           f"Для добавления введите: add <user_id> <amount>\n"
           f"Для удаления введите: remove <user_id> <amount>\n\n"
           f"Например: add 123456789 1000")
    
    # Create keyboard with back button
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(types.InlineKeyboardButton("🔙 Назад", callback_data="admin_back"))
    
    # Send message
    msg = bot.send_message(chat_id, msg, parse_mode='HTML', reply_markup=keyboard)
    
    # Register next step handler
    bot.register_next_step_handler(msg, lambda m: process_money_command(m, admin_id, bot))

def process_money_command(message, admin_id, bot):
    """Process add/remove money command."""
    text = message.text.strip().split()
    
    if len(text) != 3:
        bot.send_message(message.chat.id, "❌ Неверный формат команды. Пример: add 123456789 1000")
        return
    
    command, user_id_str, amount_str = text
    
    try:
        user_id = int(user_id_str)
        amount = int(amount_str)
    except ValueError:
        bot.send_message(message.chat.id, "❌ ID пользователя и сумма должны быть числами.")
        return
    
    if command.lower() == "add":
        if not is_admin_with_permission(admin_id, "add_money"):
            bot.send_message(message.chat.id, "❌ У вас нет прав для добавления денег.")
            return
        success, message_text = add_money(admin_id, user_id, amount)
    elif command.lower() == "remove":
        if not is_admin_with_permission(admin_id, "remove_money"):
            bot.send_message(message.chat.id, "❌ У вас нет прав для удаления денег.")
            return
        success, message_text = remove_money(admin_id, user_id, amount)
    else:
        bot.send_message(message.chat.id, "❌ Неизвестная команда. Используйте add или remove.")
        return
    
    bot.send_message(message.chat.id, f"{'✅' if success else '❌'} {message_text}")

def show_give_buff_menu(chat_id, admin_id, bot):
    """Show menu for giving buffs to users."""
    if not is_admin_with_permission(admin_id, "give_items"):
        bot.send_message(chat_id, "❌ У вас нет прав для выдачи предметов.")
        return
    
    # Create message with available buffs
    msg = (f"🎁 <b>Выдача баффов</b>\n\n"
           f"Доступные баффы:\n")
    
    for item in SHOP_ITEMS:
        msg += f"{item['id']}. {item['name']} (+{int(item['bonus']*100)}%, {item['duration']} мин.)\n"
    
    msg += (f"\nВведите ID пользователя и ID баффа для выдачи.\n"
            f"Формат: <user_id> <buff_id>\n\n"
            f"Например: 123456789 0")
    
    # Create keyboard with back button
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(types.InlineKeyboardButton("🔙 Назад", callback_data="admin_back"))
    
    # Send message
    msg = bot.send_message(chat_id, msg, parse_mode='HTML', reply_markup=keyboard)
    
    # Register next step handler
    bot.register_next_step_handler(msg, lambda m: process_give_buff(m, admin_id, bot))

def process_give_buff(message, admin_id, bot):
    """Process give buff command."""
    text = message.text.strip().split()
    
    if len(text) != 2:
        bot.send_message(message.chat.id, "❌ Неверный формат команды. Пример: 123456789 0")
        return
    
    user_id_str, buff_id_str = text
    
    try:
        user_id = int(user_id_str)
        buff_id = int(buff_id_str)
    except ValueError:
        bot.send_message(message.chat.id, "❌ ID пользователя и ID баффа должны быть числами.")
        return
    
    success, message_text = give_buff(admin_id, user_id, buff_id)
    
    bot.send_message(message.chat.id, f"{'✅' if success else '❌'} {message_text}")

def show_broadcast_menu(chat_id, admin_id, bot):
    """Show menu for sending broadcast messages."""
    if not is_admin_with_permission(admin_id, "broadcast"):
        bot.send_message(chat_id, "❌ У вас нет прав для рассылки сообщений.")
        return
    
    # Create message and keyboard
    msg = (f"📣 <b>Рассылка сообщений</b>\n\n"
           f"Введите текст сообщения для отправки всем пользователям бота.\n"
           f"Можно использовать HTML-разметку.\n\n"
           f"Например: Уважаемые пользователи! Сегодня в магазине <b>скидки</b>!")
    
    # Create keyboard with back button
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(types.InlineKeyboardButton("🔙 Назад", callback_data="admin_back"))
    
    # Send message
    msg = bot.send_message(chat_id, msg, parse_mode='HTML', reply_markup=keyboard)
    
    # Register next step handler
    bot.register_next_step_handler(msg, lambda m: process_broadcast(m, admin_id, bot))

def process_broadcast(message, admin_id, bot):
    """Process broadcast message."""
    text = message.text.strip()
    
    if not text:
        bot.send_message(message.chat.id, "❌ Сообщение не может быть пустым.")
        return
    
    success, message_text, user_ids = prepare_broadcast(admin_id, text)
    
    if not success:
        bot.send_message(message.chat.id, f"❌ {message_text}")
        return
    
    # Confirm broadcast
    keyboard = types.InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        types.InlineKeyboardButton("✅ Подтвердить", callback_data=f"admin_confirm_broadcast"),
        types.InlineKeyboardButton("❌ Отменить", callback_data="admin_back")
    )
    
    bot.send_message(
        message.chat.id,
        f"📣 <b>Предпросмотр сообщения:</b>\n\n{text}\n\n{message_text}\n\nПодтвердите отправку:",
        parse_mode='HTML',
        reply_markup=keyboard
    )
    
    # Store broadcast data in user_data
    user_data = get_user_data(admin_id)
    user_data["_broadcast_data"] = {
        "text": text,
        "user_ids": user_ids
    }
    
def process_add_item(message, admin_id, bot):
    """Process adding a new shop item."""
    if not is_admin_with_permission(admin_id, "manage_items"):
        bot.send_message(message.chat.id, "❌ У вас нет прав для управления товарами магазина.")
        return
    
    text = message.text.strip()
    parts = [part.strip() for part in text.split('|')]
    
    if len(parts) != 5:
        bot.send_message(message.chat.id, 
                        "❌ Неверный формат. Используйте: <название> | <описание> | <цена> | <бонус в %> | <длительность>")
        return
    
    name, description, price_str, bonus_str, duration_str = parts
    
    try:
        price = int(price_str)
        bonus = float(bonus_str) / 100  # Convert percentage to decimal
        duration = int(duration_str)
    except ValueError:
        bot.send_message(message.chat.id, "❌ Цена, бонус и длительность должны быть числами.")
        return
    
    success, message_text = add_shop_item(admin_id, name, description, price, bonus, duration)
    
    bot.send_message(message.chat.id, f"{'✅' if success else '❌'} {message_text}")
    if success:
        # Show shop items menu again
        show_shop_items_menu(message.chat.id, admin_id, bot)

def process_edit_item(message, admin_id, bot):
    """Process editing a shop item."""
    if not is_admin_with_permission(admin_id, "manage_items"):
        bot.send_message(message.chat.id, "❌ У вас нет прав для управления товарами магазина.")
        return
    
    text = message.text.strip()
    parts = [part.strip() for part in text.split('|')]
    
    if len(parts) != 6:
        bot.send_message(message.chat.id, 
                        "❌ Неверный формат. Используйте: <ID> | <название> | <описание> | <цена> | <бонус в %> | <длительность>")
        return
    
    item_id_str, name, description, price_str, bonus_str, duration_str = parts
    
    try:
        item_id = int(item_id_str)
    except ValueError:
        bot.send_message(message.chat.id, "❌ ID товара должен быть числом.")
        return
    
    # Convert empty strings to None to keep current values
    name = None if not name else name
    description = None if not description else description
    
    # Parse numeric values
    try:
        price = int(price_str) if price_str else None
        bonus = float(bonus_str) / 100 if bonus_str else None  # Convert percentage to decimal
        duration = int(duration_str) if duration_str else None
    except ValueError:
        bot.send_message(message.chat.id, "❌ Цена, бонус и длительность должны быть числами.")
        return
    
    success, message_text = edit_shop_item(
        admin_id, item_id, name, description, price, bonus, duration
    )
    
    bot.send_message(message.chat.id, f"{'✅' if success else '❌'} {message_text}")
    if success:
        # Show shop items menu again
        show_shop_items_menu(message.chat.id, admin_id, bot)

def process_delete_item(message, admin_id, bot):
    """Process deleting a shop item."""
    if not is_admin_with_permission(admin_id, "manage_items"):
        bot.send_message(message.chat.id, "❌ У вас нет прав для управления товарами магазина.")
        return
    
    text = message.text.strip()
    
    try:
        item_id = int(text)
    except ValueError:
        bot.send_message(message.chat.id, "❌ ID товара должен быть числом.")
        return
    
    success, message_text = delete_shop_item(admin_id, item_id)
    
    bot.send_message(message.chat.id, f"{'✅' if success else '❌'} {message_text}")
    if success:
        # Show shop items menu again
        show_shop_items_menu(message.chat.id, admin_id, bot)

def process_admin_command(message, admin_id, bot):
    """Process admin management command."""
    text = message.text.strip().split(maxsplit=2)
    
    if len(text) < 2:
        bot.send_message(message.chat.id, "❌ Неверный формат команды.")
        return
    
    command = text[0].lower()
    
    if command == "add":
        # Add admin
        if len(text) < 3:
            bot.send_message(message.chat.id, "❌ Неверный формат команды. Пример: add 123456789 Модератор")
            return
        
        try:
            user_id = int(text[1])
            name = text[2]
        except ValueError:
            bot.send_message(message.chat.id, "❌ ID пользователя должен быть числом.")
            return
        
        success, message_text = add_admin(admin_id, user_id, name)
        bot.send_message(message.chat.id, f"{'✅' if success else '❌'} {message_text}")
        
    elif command == "remove":
        # Remove admin
        try:
            user_id = int(text[1])
        except ValueError:
            bot.send_message(message.chat.id, "❌ ID пользователя должен быть числом.")
            return
        
        success, message_text = remove_admin(admin_id, user_id)
        bot.send_message(message.chat.id, f"{'✅' if success else '❌'} {message_text}")
        
    else:
        bot.send_message(message.chat.id, "❌ Неизвестная команда. Используйте add или remove.")
        return
    
def show_shop_items_menu(chat_id, admin_id, bot):
    """Show menu for shop items management."""
    if not is_admin_with_permission(admin_id, "manage_items"):
        bot.send_message(chat_id, "❌ У вас нет прав для управления товарами магазина.")
        return
    
    # Get all shop items
    shop_items = get_all_shop_items()
    
    # Create message with shop items list
    msg = f"🛒 <b>Управление товарами магазина</b>\n\n"
    
    if shop_items:
        for i, item in enumerate(shop_items):
            msg += (f"ID: {item['id']}, <b>{item['name']}</b>\n"
                   f"📝 {item['description']}\n"
                   f"💰 Цена: {item['price']} руб.\n"
                   f"📈 Бонус: +{int(item['bonus']*100)}%\n"
                   f"⏱ Длительность: {item['duration']} мин.\n"
                   f"🔄 Активен: {'✅' if item.get('is_active', True) else '❌'}\n\n")
    else:
        msg += "Товары не найдены."
    
    # Create keyboard with options
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    
    keyboard.add(
        types.InlineKeyboardButton("➕ Добавить товар", callback_data="admin_add_item"),
        types.InlineKeyboardButton("✏️ Редактировать товар", callback_data="admin_edit_item"),
        types.InlineKeyboardButton("🗑 Удалить товар", callback_data="admin_delete_item"),
        types.InlineKeyboardButton("🔙 Назад", callback_data="admin_back")
    )
    
    # Send message
    bot.send_message(chat_id, msg, parse_mode='HTML', reply_markup=keyboard)

def show_admin_management(chat_id, admin_id, bot):
    """Show admin management menu."""
    if not is_admin_with_permission(admin_id, "manage_admins"):
        bot.send_message(chat_id, "❌ У вас нет прав для управления администраторами.")
        return
    
    # Get list of admins
    admins = get_all_admins()
    
    # Create message with admin list
    msg = f"👑 <b>Управление администраторами</b>\n\n"
    
    if admins:
        msg += "<b>Текущие администраторы:</b>\n"
        for i, admin in enumerate(admins, start=1):
            role_emoji = "👑" if admin["role"] == ROLE_OWNER else "🛡️"
            msg += f"{i}. {role_emoji} <b>{admin['name']}</b> (ID: {admin['user_id']})\n"
            
            # List permissions
            permissions = admin["permissions"]
            enabled_permissions = [k for k, v in permissions.items() if v]
            
            if enabled_permissions:
                msg += "   Права: " + ", ".join(enabled_permissions) + "\n"
            
            msg += "\n"
    else:
        msg += "❌ Администраторы не найдены.\n\n"
    
    msg += (f"Для добавления администратора введите:\n"
            f"add <user_id> <name>\n\n"
            f"Для удаления администратора введите:\n"
            f"remove <user_id>\n\n"
            f"Например: add 123456789 Модератор")
    
    # Create keyboard with back button
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(types.InlineKeyboardButton("🔙 Назад", callback_data="admin_back"))
    
    # Send message
    msg = bot.send_message(chat_id, msg, parse_mode='HTML', reply_markup=keyboard)
    
    # Register next step handler
    bot.register_next_step_handler(msg, lambda m: process_admin_command(m, admin_id, bot))