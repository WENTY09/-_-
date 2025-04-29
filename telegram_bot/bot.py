"""
Telegram bot main implementation.
"""
import os
import logging
import telebot
from telebot import types
from telegram_bot.handlers import register_handlers

# Set up logging
logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def run_telegram_bot():
    """Initialize and run the Telegram bot."""
    # Get the bot token from environment variables
    token = os.environ.get('TELEGRAM_BOT_TOKEN')
    
    if not token:
        logger.error("No TELEGRAM_BOT_TOKEN found in environment variables!")
        return
    
    try:
        # Create the bot instance
        bot = telebot.TeleBot(token)
        logger.info("Telegram bot initialized successfully")
        
        # Register message handlers
        register_handlers(bot)
        
        # Set up bot commands menu
        commands = [
            types.BotCommand(command="start", description="Начать использование бота"),
            types.BotCommand(command="raznos", description="Разносить посылки"),
            types.BotCommand(command="top", description="Список лучших курьеров"),
            types.BotCommand(command="profile", description="Ваш профиль"),
            types.BotCommand(command="magaz", description="Магазин улучшений"),
            types.BotCommand(command="adm", description="Административная панель")
        ]
        bot.set_my_commands(commands)
        
        # Start the bot
        logger.info("Bot started successfully!")
        logger.info("Starting Telegram bot polling...")
        bot.polling(non_stop=True, interval=0, timeout=30)
    except Exception as e:
        logger.error(f"Error starting Telegram bot: {e}")