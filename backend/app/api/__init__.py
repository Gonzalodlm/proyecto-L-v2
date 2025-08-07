"""
API Blueprint modules for Impulso Inversor
"""
from .portfolios import portfolios_bp
from .analysis import analysis_bp  
from .auth import auth_bp
from .etfs import etfs_bp

__all__ = ['portfolios_bp', 'analysis_bp', 'auth_bp', 'etfs_bp']