"""
Initialize database tables
"""
from app import create_app, db
from config.config import config
import os

# Create app with development config
config_name = os.environ.get('FLASK_ENV', 'development')
app = create_app(config[config_name])

with app.app_context():
    # Create all tables
    db.create_all()
    print("Database tables created successfully!")
    
    # You can add sample data here if needed
    print("Database initialization complete.")