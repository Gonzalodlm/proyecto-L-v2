"""
Impulso Inversor Backend - Flask Application Factory
"""
from flask import Flask
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_caching import Cache
from flasgger import Swagger

from config.config import Config

# Initialize extensions
db = SQLAlchemy()
migrate = Migrate()
jwt = JWTManager()
cache = Cache()
swagger = Swagger()


def create_app(config_class=Config):
    """Application factory pattern"""
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # Initialize extensions with app
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    cache.init_app(app)
    swagger.init_app(app)
    
    # Configure CORS
    CORS(app, origins=app.config.get('CORS_ORIGINS', ['http://localhost:5173']))
    
    # Register blueprints
    from app.api import portfolios_bp, analysis_bp, auth_bp, etfs_bp
    
    app.register_blueprint(portfolios_bp, url_prefix='/api/portfolios')
    app.register_blueprint(analysis_bp, url_prefix='/api/analysis')
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(etfs_bp, url_prefix='/api/etfs')
    
    # Health check endpoint
    @app.route('/health')
    def health_check():
        return {'status': 'healthy', 'service': 'impulso-inversor-backend'}
    
    return app