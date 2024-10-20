from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from extensions import db  # Import the single SQLAlchemy instance from extensions

# Function to initialize the app with the database
def init_db(app):
    db.init_app(app)
    Migrate(app, db)  # Initialize Flask-Migrate

