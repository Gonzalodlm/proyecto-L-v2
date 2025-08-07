"""
Portfolio model for storing user portfolio allocations and performance
"""
from datetime import datetime
from sqlalchemy.dialects.postgresql import JSON
from .. import db

class Portfolio(db.Model):
    __tablename__ = 'portfolios'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    risk_profile_id = db.Column(db.Integer, db.ForeignKey('risk_profiles.id'), nullable=False)
    
    # Portfolio composition
    allocations = db.Column(JSON, nullable=False)  # ETF ticker -> percentage
    initial_investment = db.Column(db.Numeric(12, 2), nullable=True)  # Optional user input
    
    # Performance tracking (calculated periodically)
    current_value = db.Column(db.Numeric(12, 2), nullable=True)
    total_return_pct = db.Column(db.Numeric(8, 4), nullable=True)
    annual_return_pct = db.Column(db.Numeric(8, 4), nullable=True)
    volatility_pct = db.Column(db.Numeric(8, 4), nullable=True)
    sharpe_ratio = db.Column(db.Numeric(8, 4), nullable=True)
    max_drawdown_pct = db.Column(db.Numeric(8, 4), nullable=True)
    
    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    last_rebalance = db.Column(db.DateTime, nullable=True)
    
    # Model portfolio templates based on risk buckets
    MODEL_PORTFOLIOS = {
        0: {  # Conservative
            "BIL": 0.30,   # Cash/T-Bills
            "AGG": 0.50,   # Bonds
            "ACWI": 0.10,  # Global equities
            "GLD": 0.10,   # Gold
        },
        1: {  # Moderate
            "BIL": 0.15,
            "AGG": 0.35,
            "ACWI": 0.30,
            "VNQ": 0.10,   # REITs
            "GLD": 0.10,
        },
        2: {  # Balanced
            "BIL": 0.05,
            "AGG": 0.25,
            "ACWI": 0.45,
            "VNQ": 0.15,
            "GLD": 0.10,
        },
        3: {  # Growth
            "AGG": 0.15,
            "ACWI": 0.65,
            "VNQ": 0.15,
            "GLD": 0.05,
        },
        4: {  # Aggressive
            "ACWI": 0.80,
            "VNQ": 0.15,
            "GLD": 0.05,
        },
    }
    
    def __init__(self, user_id, risk_profile_id, allocations=None, initial_investment=None):
        self.user_id = user_id
        self.risk_profile_id = risk_profile_id
        self.allocations = allocations
        self.initial_investment = initial_investment
    
    @classmethod
    def create_from_risk_profile(cls, user_id, risk_profile, initial_investment=None):
        """Create portfolio based on risk profile"""
        model_allocation = cls.MODEL_PORTFOLIOS[risk_profile.risk_bucket].copy()
        
        return cls(
            user_id=user_id,
            risk_profile_id=risk_profile.id,
            allocations=model_allocation,
            initial_investment=initial_investment
        )
    
    @property
    def total_allocation(self):
        """Verify allocations sum to 1.0 (100%)"""
        return sum(self.allocations.values()) if self.allocations else 0
    
    @property
    def is_balanced(self):
        """Check if portfolio allocations are properly balanced"""
        return abs(self.total_allocation - 1.0) < 0.001  # Allow small rounding errors
    
    def get_allocation_breakdown(self):
        """Get detailed breakdown of allocations with ETF info"""
        from ..services.etf_service import ETFService
        
        breakdown = []
        for ticker, weight in (self.allocations or {}).items():
            etf_info = ETFService.get_etf_info(ticker)
            breakdown.append({
                'ticker': ticker,
                'weight': weight,
                'weight_pct': weight * 100,
                'etf_info': etf_info
            })
        
        return sorted(breakdown, key=lambda x: x['weight'], reverse=True)
    
    def calculate_rebalancing_needed(self, current_prices=None):
        """
        Calculate if portfolio needs rebalancing based on drift from target
        Returns list of adjustments needed
        """
        if not current_prices or not self.allocations:
            return []
        
        suggestions = []
        threshold = 0.05  # 5% deviation threshold
        
        for ticker, target_weight in self.allocations.items():
            # In real implementation, would calculate current weight based on market values
            # For now, assume target allocation
            current_weight = target_weight  # Placeholder
            
            difference = abs(current_weight - target_weight)
            if difference > threshold:
                action = "Aumentar" if current_weight < target_weight else "Reducir"
                suggestions.append({
                    'ticker': ticker,
                    'action': action,
                    'target_weight': target_weight,
                    'current_weight': current_weight,
                    'difference_pct': difference * 100
                })
        
        return suggestions
    
    def update_performance_metrics(self, metrics):
        """Update portfolio performance metrics"""
        self.current_value = metrics.get('current_value')
        self.total_return_pct = metrics.get('total_return_pct')  
        self.annual_return_pct = metrics.get('annual_return_pct')
        self.volatility_pct = metrics.get('volatility_pct')
        self.sharpe_ratio = metrics.get('sharpe_ratio')
        self.max_drawdown_pct = metrics.get('max_drawdown_pct')
        self.updated_at = datetime.utcnow()
    
    def to_dict(self, include_performance=True):
        """Convert portfolio to dictionary"""
        data = {
            'id': self.id,
            'user_id': self.user_id,
            'risk_profile_id': self.risk_profile_id,
            'allocations': self.allocations,
            'allocation_breakdown': self.get_allocation_breakdown(),
            'initial_investment': float(self.initial_investment) if self.initial_investment else None,
            'is_balanced': self.is_balanced,
            'total_allocation': self.total_allocation,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'is_active': self.is_active,
            'last_rebalance': self.last_rebalance.isoformat() if self.last_rebalance else None
        }
        
        if include_performance:
            data.update({
                'current_value': float(self.current_value) if self.current_value else None,
                'total_return_pct': float(self.total_return_pct) if self.total_return_pct else None,
                'annual_return_pct': float(self.annual_return_pct) if self.annual_return_pct else None,
                'volatility_pct': float(self.volatility_pct) if self.volatility_pct else None,
                'sharpe_ratio': float(self.sharpe_ratio) if self.sharpe_ratio else None,
                'max_drawdown_pct': float(self.max_drawdown_pct) if self.max_drawdown_pct else None,
            })
        
        return data
    
    def __repr__(self):
        return f'<Portfolio user_id={self.user_id} risk_profile_id={self.risk_profile_id}>'