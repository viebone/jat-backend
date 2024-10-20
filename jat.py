from dotenv import load_dotenv
from flask import Flask
from flask_cors import CORS
from extensions import db, login_manager, migrate, limiter, csrf  # Import csrf from extensions
from models import Users  # Import the Users model explicitly
from routes import bp as main_bp  # Import the blueprint from routes.py
from config import ProductionConfig, DevelopmentConfig
from flask_talisman import Talisman
import os

app = Flask(__name__)

# Load the environment from system environment variable or default to 'development'
env = os.environ.get('FLASK_ENV', 'development')

# Set up configurations based on the environment
if env == 'production':
    app.config.from_object('config.ProductionConfig')  # Load production settings
    # Initialize Talisman with default settings
    talisman = Talisman(app)
else:
    app.config.from_object('config.DevelopmentConfig')  # Load development settings
    talisman = None  # Do not enforce HTTPS in development
# Enable CORS for the entire app
CORS(app, resources={r"/*": {"origins": "http://localhost:3000"}},
     methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
     allow_headers=["Content-Type", "Authorization", "X-CSRFToken"],
     expose_headers=["Content-Type", "Authorization", "X-CSRFToken"],
     supports_credentials=True)

# Initialize extensions
try:
    db.init_app(app)
    migrate.init_app(app, db)
    print("Database initialized successfully")
    print("Database initialized with Flask app")
except Exception as e:
    print(f"Error initializing the database: {str(e)}")

login_manager.init_app(app)
csrf.init_app(app)

# Set login properties
login_manager.login_view = 'main.login'
login_manager.login_message_category = 'info'

# Bind the rate limiter to the app
limiter.init_app(app)
limiter.default_limits = ["200 per day", "50 per hour"]

# Register the blueprint
app.register_blueprint(main_bp)  # Register the blueprint from routes.py

@login_manager.user_loader
def load_user(user_id):
    return Users.query.get(int(user_id))

if __name__ == "__main__":
    app.run(debug=True)
