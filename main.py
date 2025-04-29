"""
Delivery Bot - Main Entry Point
"""
import logging
import os
from app import app, db
from telegram_bot import run_telegram_bot
import threading

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def start_bot():
    """Start the Telegram bot in a separate thread."""
    run_telegram_bot()

# Initialize database
with app.app_context():
    # Import models after app is created
    import models
    db.create_all()
    logger.info("Database initialization complete")

# Import and initialize admin module
import admin
admin.init_admin()

# Import filters for templates
from datetime import datetime

@app.template_filter('datetime')
def format_datetime(timestamp):
    """Format a timestamp as a readable date time."""
    if not timestamp:
        return "Никогда"
    dt = datetime.fromtimestamp(timestamp)
    return dt.strftime("%d.%m.%Y %H:%M:%S")

if __name__ == '__main__':
    # Check if bot token is available
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not token:
        logger.error("No TELEGRAM_BOT_TOKEN found! Bot will not work!")
    else:
        # Start bot in a separate thread
        bot_thread = threading.Thread(target=start_bot)
        bot_thread.daemon = True
        bot_thread.start()
        logger.info("Bot thread started")

    # Start web server
    app.run(host='0.0.0.0', port=5000)