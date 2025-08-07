"""
User model for authentication and profile management
"""
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

from .. import db

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    first_name = db.Column(db.String(50), nullable=True)
    last_name = db.Column(db.String(50), nullable=True)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    risk_profiles = db.relationship('RiskProfile', backref='user', lazy=True, cascade='all, delete-orphan')
    portfolios = db.relationship('Portfolio', backref='user', lazy=True, cascade='all, delete-orphan')
    
    def __init__(self, email, password=None, first_name=None, last_name=None):
        self.email = email.lower().strip()
        if password:
            self.set_password(password)
        self.first_name = first_name
        self.last_name = last_name
    
    def set_password(self, password):
        """Hash and set password"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Check if provided password matches hash"""
        return check_password_hash(self.password_hash, password)
    
    @property
    def full_name(self):
        """Get user's full name"""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.email
    
    @property
    def current_risk_profile(self):
        """Get the most recent risk profile"""
        return self.risk_profiles.order_by(RiskProfile.created_at.desc()).first()
    
    @property
    def current_portfolio(self):
        """Get the most recent portfolio"""
        return self.portfolios.order_by(Portfolio.created_at.desc()).first()
    
    def to_dict(self, include_sensitive=False):
        """Convert user to dictionary"""
        data = {
            'id': self.id,
            'email': self.email,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'full_name': self.full_name,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'has_risk_profile': bool(self.current_risk_profile),
            'has_portfolio': bool(self.current_portfolio)
        }
        
        if include_sensitive:
            data['risk_profile'] = self.current_risk_profile.to_dict() if self.current_risk_profile else None
            data['portfolio'] = self.current_portfolio.to_dict() if self.current_portfolio else None
            
        return data
    
    def __repr__(self):
        return f'<User {self.email}>'