"""
Telegram bot main implementation.
"""
import os
import logging
import telebot
from telegram_bot.handlers import register_handlers

# Set up logging
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
        
        # Initialize database connection
        with app.app_context():
            try:
                db.create_all()
                logger.info("Database initialized successfully")
            except Exception as e:
                logger.error(f"Database initialization error: {e}")
                return
        
        # Start the bot
        logger.info("Starting Telegram bot polling...")
        bot.infinity_polling(timeout=10, long_polling_timeout=5)
    except Exception as e:
        logger.error(f"Error starting Telegram bot: {e}")
        if 'bot' in locals():
            bot.stop_polling()