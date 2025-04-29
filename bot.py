import os
import logging
from telebot import TeleBot
from user_data import (
    get_user_data,
    update_user_data,
    can_deliver,
    get_top_users,
    get_shop_items_count,
    get_shop_item,
    purchase_buff,
    get_active_buffs_info,
    is_bot_active,
    set_bot_state
)
from config import TELEGRAM_BOT_TOKEN, ADMIN_IDS

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Инициализация бота
if not TELEGRAM_BOT_TOKEN:
    raise ValueError("Не установлен токен бота! Проверьте конфигурацию в config.py")

bot = TeleBot(TELEGRAM_BOT_TOKEN)

def check_admin(user_id: int) -> bool:
    """Проверяет, является ли пользователь администратором."""
    return str(user_id) in ADMIN_IDS

def check_bot_active(func):
    """Декоратор для проверки активности бота."""
    def wrapper(message, *args, **kwargs):
        if not is_bot_active() and not check_admin(message.from_user.id):
            bot.reply_to(message, "🔒 Бот временно отключен.")
            return
        return func(message, *args, **kwargs)
    return wrapper

# Команды бота
@bot.message_handler(commands=['start'])
@check_bot_active
def start_command(message):
    user_data = get_user_data(message.from_user.id)
    bot.reply_to(
        message,
        f"👋 Привет, {user_data['username']}!\n\n"
        "🚚 Я бот для доставки. Используй /help чтобы узнать доступные команды."
    )

@bot.message_handler(commands=['help'])
@check_bot_active
def help_command(message):
    help_text = (
        "📋 Доступные команды:\n\n"
        "/deliver - Сделать доставку\n"
        "/profile - Посмотреть профиль\n"
        "/top - Топ курьеров\n"
        "/shop - Магазин баффов\n"
        "/buffs - Активные баффы"
    )
    if check_admin(message.from_user.id):
        help_text += "\n\nКоманды администратора:\n/off - Отключить бота\n/on - Включить бота"
    bot.reply_to(message, help_text)

@bot.message_handler(commands=['profile'])
@check_bot_active
def profile_command(message):
    user_data = get_user_data(message.from_user.id)
    
    # Получаем информацию об активных баффах
    active_buffs = get_active_buffs_info(message.from_user.id)
    buffs_text = "\n".join([
        f"🔥 {buff['name']} (+{buff['bonus']}%) - осталось {buff['remaining_time']}"
        for buff in active_buffs
    ]) if active_buffs else "Нет активных баффов"
    
    profile_text = (
        f"👤 Профиль: {user_data['username']}\n\n"
        f"📦 Доставок: {user_data['deliveries']}\n"
        f"💰 Баланс: {user_data['money']} руб.\n"
        f"⭐️ Опыт: {user_data['experience']}\n\n"
        f"🔥 Активные баффы:\n{buffs_text}"
    )
    bot.reply_to(message, profile_text)

@bot.message_handler(commands=['deliver'])
@check_bot_active
def deliver_command(message):
    can_deliver_now, time_remaining = can_deliver(message.from_user.id)
    
    if not can_deliver_now:
        if time_remaining:
            minutes = int(time_remaining.total_seconds() // 60)
            seconds = int(time_remaining.total_seconds() % 60)
            bot.reply_to(
                message,
                f"⏳ Подождите еще {minutes}м {seconds}с перед следующей доставкой!"
            )
        else:
            bot.reply_to(message, "❌ Вы заблокированы!")
        return
    
    # Рассчитываем заработок
    base_earnings = 100  # Базовый заработок
    original_earnings, buffed_earnings = update_user_data(
        message.from_user.id,
        deliveries=1,
        earnings=base_earnings
    )
    
    # Формируем сообщение
    if buffed_earnings > original_earnings:
        bonus = buffed_earnings - original_earnings
        delivery_text = (
            f"✅ Доставка выполнена!\n\n"
            f"💰 Заработок: {original_earnings} руб.\n"
            f"🔥 Бонус: +{bonus} руб.\n"
            f"💵 Итого: {buffed_earnings} руб."
        )
    else:
        delivery_text = (
            f"✅ Доставка выполнена!\n\n"
            f"💰 Заработок: {buffed_earnings} руб."
        )
    
    bot.reply_to(message, delivery_text)

@bot.message_handler(commands=['top'])
@check_bot_active
def top_command(message):
    top_users = get_top_users(5)
    
    if not top_users:
        bot.reply_to(message, "📊 Статистика пока недоступна")
        return
    
    top_text = "🏆 Топ курьеров:\n\n"
    for position, username, deliveries in top_users:
        if position == 1:
            emoji = "🥇"
        elif position == 2:
            emoji = "🥈"
        elif position == 3:
            emoji = "🥉"
        else:
            emoji = "👤"
        
        top_text += f"{emoji} {username}: {deliveries} доставок\n"
    
    bot.reply_to(message, top_text)

@bot.message_handler(commands=['shop'])
@check_bot_active
def shop_command(message):
    items_count = get_shop_items_count()
    if items_count == 0:
        bot.reply_to(message, "🏪 Магазин временно закрыт")
        return
    
    shop_text = "🏪 Магазин баффов:\n\n"
    for i in range(items_count):
        item = get_shop_item(i)
        shop_text += (
            f"{i+1}. {item['name']}\n"
            f"📝 {item['description']}\n"
            f"💰 Цена: {item['price']} руб.\n"
            f"⏱ Длительность: {item['duration']} мин.\n\n"
        )
    
    shop_text += "Для покупки используйте /buy <номер предмета>"
    bot.reply_to(message, shop_text)

@bot.message_handler(commands=['buy'])
@check_bot_active
def buy_command(message):
    try:
        item_number = int(message.text.split()[1]) - 1
        success, result_message = purchase_buff(message.from_user.id, item_number)
        bot.reply_to(message, result_message)
    except (IndexError, ValueError):
        bot.reply_to(
            message,
            "❌ Неверный формат команды!\nИспользуйте: /buy <номер предмета>"
        )

@bot.message_handler(commands=['buffs'])
@check_bot_active
def buffs_command(message):
    active_buffs = get_active_buffs_info(message.from_user.id)
    
    if not active_buffs:
        bot.reply_to(message, "🔥 У вас нет активных баффов")
        return
    
    buffs_text = "🔥 Ваши активные баффы:\n\n"
    for buff in active_buffs:
        buffs_text += (
            f"• {buff['name']}\n"
            f"📈 Бонус: +{buff['bonus']}%\n"
            f"⏱ Осталось: {buff['remaining_time']}\n\n"
        )
    
    bot.reply_to(message, buffs_text)

@bot.message_handler(commands=['off'])
def off_command(message):
    if not check_admin(message.from_user.id):
        bot.reply_to(message, "❌ У вас нет прав для выполнения этой команды!")
        return
    
    if set_bot_state(False):
        bot.reply_to(message, "🔒 Бот успешно отключен.")
    else:
        bot.reply_to(message, "❌ Ошибка при отключении бота.")

@bot.message_handler(commands=['on'])
def on_command(message):
    if not check_admin(message.from_user.id):
        bot.reply_to(message, "❌ У вас нет прав для выполнения этой команды!")
        return
    
    if set_bot_state(True):
        bot.reply_to(message, "🔓 Бот успешно включен.")
    else:
        bot.reply_to(message, "❌ Ошибка при включении бота.")

def main():
    logger.info("Инициализация бота...")
    try:
        logger.info("Бот успешно запущен!")
        logger.info("Начинаем получение обновлений...")
        bot.infinity_polling()
    except Exception as e:
        logger.error(f"Ошибка при работе бота: {e}")

if __name__ == "__main__":
    main() 