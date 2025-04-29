import logging
import os
import telebot
from telebot import types
from handlers import register_handlers

# Set up logging with a simple format
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
    
    # Create the bot instance
    bot = telebot.TeleBot(token)
    
    # Register all handlers
    register_handlers(bot)
    
    # Run the bot
    logger.info("Bot started successfully!")
    bot.infinity_polling()

if __name__ == '__main__':
    run_bot()
