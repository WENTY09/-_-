"""
Telegram Bot Main Module
This module initializes and runs the Telegram bot.
"""
import logging
import os
from dotenv import load_dotenv
import telebot
from telebot import types
from handlers import register_handlers
from user_data import initialize_database

# Load environment variables
load_dotenv()

# Set environment variables directly if not loaded from .env
if not os.environ.get("TELEGRAM_BOT_TOKEN"):
    os.environ["TELEGRAM_BOT_TOKEN"] = "7991697168:AAF1GxpKVE1M1N-QSJ-eKiKm47g775jtPJ8"
    os.environ["DATABASE_URL"] = "postgresql://neondb_owner:npg_Sv5uoEPq4Wxr@ep-odd-resonance-a4sl06ma.us-east-1.aws.neon.tech/neondb?sslmode=require"
    os.environ["SESSION_SECRET"] = "zE31T4akjO0gpeoW7cnCKgw2DPy5EyGXOEkAchU5YjoOs2RdQx4mMRwpaycIWMhiy/+fr6eBZVsLxPph8e+0cw=="

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def run_bot():
    """Initialize and run the Telegram bot."""
    # Get the bot token from environment variables
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    
    if not token:
        logger.error("No TELEGRAM_BOT_TOKEN found in environment variables!")
        return
    
    try:
        # Initialize database
        initialize_database()
        logger.info("Database initialized successfully")
        
        # Create the bot instance
        bot = telebot.TeleBot(token)
        logger.info("Telegram bot initialized successfully")
        
        # Register all handlers
        register_handlers(bot)
        
        # Set up bot commands menu
        commands = [
            types.BotCommand(command="start", description="Начать использование бота"),
            types.BotCommand(command="raznos", description="Разносить посылки"),
            types.BotCommand(command="top", description="Список лучших курьеров"),
            types.BotCommand(command="profile", description="Ваш профиль"),
            types.BotCommand(command="magaz", description="Магазин улучшений")
        ]
        bot.set_my_commands(commands)
        
        # Run the bot
        logger.info("Bot started successfully!")
        logger.info("Starting bot polling...")
        bot.infinity_polling(timeout=10, long_polling_timeout=5)
    except Exception as e:
        logger.error(f"Error starting Telegram bot: {e}")

if __name__ == '__main__':
    run_bot()
