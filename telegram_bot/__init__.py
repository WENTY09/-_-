
"""
Telegram bot package
"""
import os
import telebot
import logging

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def run_telegram_bot():
    """Initialize and run the Telegram bot."""
    try:
        # Get token from environment
        token = os.environ.get("TELEGRAM_BOT_TOKEN")
        
        if not token:
            logger.error("No Telegram bot token found!")
            return
        
        # Create bot instance
        bot = telebot.TeleBot(token)
        
        # Register all handlers
        from telegram_bot.handlers import register_handlers
        register_handlers(bot)
        
        # Log successful initialization
        logger.info("Telegram bot initialized successfully")
        
        # Start polling
        bot.infinity_polling(timeout=60)
        
    except Exception as e:
        logger.error(f"Error initializing Telegram bot: {e}")
