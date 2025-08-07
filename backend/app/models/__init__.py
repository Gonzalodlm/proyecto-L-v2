"""
Database models for Impulso Inversor
"""
from .user import User
from .risk_profile import RiskProfile  
from .portfolio import Portfolio

__all__ = ['User', 'RiskProfile', 'Portfolio']