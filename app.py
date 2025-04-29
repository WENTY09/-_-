import os
from flask import Flask, render_template
from dotenv import load_dotenv
from models import db

# Load environment variables from .env file
load_dotenv()

# Create the Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "delivery_bot_secret_key")

# Configure the database
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "sqlite:///delivery_bot.db")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Initialize the database
db.init_app(app)

# Create the database tables
with app.app_context():
    db.create_all()

# Import and register blueprints
from dashboard import dashboard_bp
app.register_blueprint(dashboard_bp)

# Basic routes
@app.route('/')
def index():
    """Render the main dashboard page."""
    return render_template('index.html')

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8080, debug=True)
