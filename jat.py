from dotenv import load_dotenv
from flask import Flask, jsonify, redirect, url_for, request, make_response
from flask_cors import CORS
from extensions import db, login_manager, migrate, limiter, csrf  # Import csrf from extensions
from models import Users  # Import the Users model explicitly
from routes import bp as main_bp  # Import the blueprint from routes.py
from config import ProductionConfig, DevelopmentConfig
from flask_talisman import Talisman
from flask_session import Session
import redis
import os

load_dotenv()  # Load .env variables

app = Flask(__name__)

# Configure the session
if os.getenv("FLASK_ENV") == "production":
    redis_url = os.getenv("REDIS_URL")
    redis_client = redis.StrictRedis.from_url(redis_url)
    app.config["SESSION_TYPE"] = "redis"
    app.config["SESSION_PERMANENT"] = False
    app.config["SESSION_USE_SIGNER"] = True
    app.config["SESSION_KEY_PREFIX"] = "jat:"
    app.config["SESSION_REDIS"] = redis_client
else:
    # Use in-memory session storage in development
    app.config["SESSION_TYPE"] = "filesystem"

# Initialize the session extension
Session(app)

# Load the environment from system environment variable or default to 'development'
env = os.environ.get('FLASK_ENV', 'development')
print(f"Environment: {env}")
print(f"Loaded DATABASE_URL: {os.environ.get('DATABASE_URL')}")

if not env:
    env = "development"
    print("Environment not set, defaulting to 'development'")

# Set up configurations based on the environment
if env == 'production':
    print("Environment = loading production variables")
    app.config.from_object('config.ProductionConfig')  # Load production settings
    # Initialize Talisman with default settings
    #talisman = Talisman(app)
    # Enable CORS for the entire app
    CORS(app, resources={r"/*": {"origins": app.config['FRONTEND_URL']}},
     methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
     allow_headers=["Content-Type", "Authorization", "X-CSRFToken", "x-csrftoken"],
     expose_headers=["Content-Type", "Authorization", "X-CSRFToken", "x-csrftoken"],
     supports_credentials=True)
    
    # Configure Flask-Limiter with Redis in production
    limiter.storage_uri = os.getenv("REDIS_URL")
else:
    print("Environment = loading development variables")
    app.config.from_object('config.DevelopmentConfig')  # Load development settings
    
    #talisman = None  # Do not enforce HTTPS in development
    # Enable CORS for the entire app
    CORS(app, resources={r"/*": {"origins": app.config['FRONTEND_URL']}},
     methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
     allow_headers=["Content-Type", "Authorization", "X-CSRFToken", "x-csrftoken"],
     expose_headers=["Content-Type", "Authorization", "X-CSRFToken", "x-csrftoken"],
     supports_credentials=True)
    
    # Use in-memory storage for Flask-Limiter in development
    limiter.storage_uri = "memory://"
    
#init db
try:
    db.init_app(app)
    migrate.init_app(app, db)  # Initialize Flask-Migrate
    print("Database initialized successfully")
    print("Database initialized with Flask app")
except Exception as e:
    print(f"Error initializing the database_: {str(e)}")
#print(f"All environment variables: {os.environ}")
print(f"FLASK_ENV: {os.environ.get('FLASK_ENV')}")
print(f"DATABASE_URL: {os.environ.get('DATABASE_URL')}")


login_manager.init_app(app)
csrf.init_app(app)
#csrf.exempt(main_bp)  # Exempt the entire blueprint

# Set login properties
login_manager.login_view = 'main.login'
login_manager.login_message_category = 'info'

# Bind the rate limiter to the app
limiter.init_app(app)
limiter.default_limits = ["200 per day", "50 per hour"]

# Register the blueprint
app.register_blueprint(main_bp)  # Register the blueprint from routes.py

# Auto-run database migrations in production
if os.environ.get("FLASK_ENV") == "production":
    try:
        with app.app_context():
            from flask_migrate import upgrade
            upgrade()
            print("Database migrations applied successfully")
    except Exception as e:
        print(f"Migration error (continuing anyway): {e}")
        # Don't crash the app if migration fails
 
@login_manager.user_loader
def load_user(user_id):
    return Users.query.get(int(user_id))

@login_manager.unauthorized_handler
def handle_unauthorized():
    # If the request is to an API endpoint, return JSON instead of redirecting
    if request.path.startswith("/api/"):
        response = jsonify({"error": "Unauthorized"})
        response.headers["Access-Control-Allow-Origin"] = app.config['FRONTEND_URL']

        response.headers["Access-Control-Allow-Credentials"] = "true"
        return response, 401
    # Otherwise, redirect to the login page
    return redirect(url_for("main.login"))

@app.before_request
def handle_preflight():
    if request.method == "OPTIONS":
        response = make_response()
        response.headers["Access-Control-Allow-Origin"] = app.config['FRONTEND_URL']

        response.headers["Access-Control-Allow-Methods"] = "POST, GET, OPTIONS, PUT, DELETE"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization, X-CSRFToken, x-csrftoken"
        response.headers["Access-Control-Allow-Credentials"] = "true"
        return response, 200

    

if __name__ == "__main__":
    if os.environ.get("FLASK_ENV") == "production":
        app.run(host="0.0.0.0", port=8080)  # Production settings
    else:
        app.run(debug=True)  # Local development settings

