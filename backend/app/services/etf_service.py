"""
ETF Information Service - Provides detailed information about supported ETFs
"""
from typing import Dict, List, Optional

class ETFService:
    """Service for ETF information and market data"""
    
    # ETF Information Database
    ETF_INFO = {
        "BIL": {
            "ticker": "BIL",
            "nombre": "SPDR Bloomberg 1-3 Month T-Bill ETF",
            "descripcion": "ETF de bonos del tesoro de muy corto plazo (1-3 meses)",
            "tipo": "Efectivo/T-Bills",
            "riesgo": "Bajo",
            "rendimiento_esperado": "2-4% anual",
            "expense_ratio": "0.1355%",
            "aum": "$4.8B",
            "inception_date": "2007-05-25",
            "color": "#2E7D32"  # Verde oscuro
        },
        "AGG": {
            "ticker": "AGG", 
            "nombre": "iShares Core U.S. Aggregate Bond ETF",
            "descripcion": "Bonos del gobierno y corporativos de EE.UU. con grado de inversión",
            "tipo": "Bonos",
            "riesgo": "Bajo",
            "rendimiento_esperado": "3-5% anual",
            "duration": "6.02 años",
            "yield": "4.50%",
            "expense_ratio": "0.03%",
            "aum": "$95.2B",
            "inception_date": "2003-09-22",
            "holdings": "10,000+ bonos",
            "color": "#1976D2"  # Azul
        },
        "ACWI": {
            "ticker": "ACWI",
            "nombre": "iShares MSCI ACWI ETF", 
            "descripcion": "Acciones globales de mercados desarrollados y emergentes",
            "tipo": "Acciones",
            "riesgo": "Medio-Alto",
            "rendimiento_esperado": "7-10% anual",
            "countries": "47 países",
            "holdings": "1,700+ empresas",
            "expense_ratio": "0.32%",
            "aum": "$18.8B",
            "inception_date": "2008-03-26",
            "color": "#388E3C"  # Verde
        },
        "VNQ": {
            "ticker": "VNQ",
            "nombre": "Vanguard Real Estate ETF",
            "descripcion": "Bienes raíces comerciales y residenciales de EE.UU.",
            "tipo": "REITs", 
            "riesgo": "Medio-Alto",
            "rendimiento_esperado": "6-9% anual",
            "dividend_yield": "3.5%",
            "expense_ratio": "0.12%",
            "aum": "$38.5B",
            "inception_date": "2004-09-23",
            "holdings": "160+ REITs",
            "color": "#F57C00"  # Naranja
        },
        "GLD": {
            "ticker": "GLD",
            "nombre": "SPDR Gold Shares",
            "descripcion": "Oro físico - Protección contra inflación y crisis",
            "tipo": "Commodities",
            "riesgo": "Medio",
            "rendimiento_esperado": "Variable",
            "correlation": "Baja correlación con acciones",
            "expense_ratio": "0.40%",
            "aum": "$58.9B", 
            "inception_date": "2004-11-18",
            "backing": "Oro físico en bóvedas",
            "color": "#FFD700"  # Dorado
        }
    }
    
    @classmethod
    def get_etf_info(cls, ticker: str) -> Optional[Dict]:
        """Get detailed information for a specific ETF"""
        return cls.ETF_INFO.get(ticker.upper())
    
    @classmethod
    def get_all_etfs(cls) -> Dict[str, Dict]:
        """Get information for all supported ETFs"""
        return cls.ETF_INFO.copy()
    
    @classmethod
    def get_etfs_by_type(cls, etf_type: str) -> Dict[str, Dict]:
        """Get ETFs filtered by type"""
        return {
            ticker: info 
            for ticker, info in cls.ETF_INFO.items()
            if info.get('tipo', '').lower() == etf_type.lower()
        }
    
    @classmethod
    def get_etfs_by_risk(cls, risk_level: str) -> Dict[str, Dict]:
        """Get ETFs filtered by risk level"""
        return {
            ticker: info
            for ticker, info in cls.ETF_INFO.items() 
            if info.get('riesgo', '').lower() == risk_level.lower()
        }
    
    @classmethod
    def get_supported_tickers(cls) -> List[str]:
        """Get list of all supported ETF tickers"""
        return list(cls.ETF_INFO.keys())
    
    @classmethod
    def validate_allocation(cls, allocations: Dict[str, float]) -> tuple[bool, List[str]]:
        """
        Validate portfolio allocation
        Returns (is_valid, list_of_errors)
        """
        errors = []
        
        # Check if all tickers are supported
        unsupported_tickers = [
            ticker for ticker in allocations.keys() 
            if ticker not in cls.ETF_INFO
        ]
        if unsupported_tickers:
            errors.append(f"ETFs no soportados: {', '.join(unsupported_tickers)}")
        
        # Check if allocations sum to 1.0 (100%)
        total_allocation = sum(allocations.values())
        if abs(total_allocation - 1.0) > 0.001:
            errors.append(f"Las asignaciones deben sumar 100% (actual: {total_allocation*100:.1f}%)")
        
        # Check for negative allocations
        negative_allocations = [
            f"{ticker}: {weight*100:.1f}%" 
            for ticker, weight in allocations.items() 
            if weight < 0
        ]
        if negative_allocations:
            errors.append(f"Asignaciones negativas no permitidas: {', '.join(negative_allocations)}")
        
        # Check for allocations over 100%
        over_allocations = [
            f"{ticker}: {weight*100:.1f}%"
            for ticker, weight in allocations.items()
            if weight > 1.0
        ]
        if over_allocations:
            errors.append(f"Asignaciones individuales no pueden exceder 100%: {', '.join(over_allocations)}")
        
        return len(errors) == 0, errors
    
    @classmethod
    def get_diversification_score(cls, allocations: Dict[str, float]) -> Dict:
        """
        Calculate diversification score based on allocation spread
        Returns score and breakdown
        """
        if not allocations:
            return {'score': 0, 'breakdown': {}, 'total_assets': 0}
        
        # Count number of different asset types
        asset_types = {}
        for ticker, weight in allocations.items():
            etf_info = cls.get_etf_info(ticker)
            if etf_info:
                asset_type = etf_info.get('tipo', 'Unknown')
                asset_types[asset_type] = asset_types.get(asset_type, 0) + weight
        
        # Calculate diversification score (0-100)
        # Based on: number of asset types and distribution evenness
        num_types = len(asset_types)
        max_concentration = max(asset_types.values()) if asset_types else 1
        
        # Score components
        type_score = min(num_types * 20, 60)  # Max 60 points for asset type diversity
        concentration_score = max(0, 40 - (max_concentration - 0.4) * 100)  # Penalty for concentration
        
        total_score = min(100, type_score + concentration_score)
        
        return {
            'score': round(total_score, 1),
            'breakdown': asset_types,
            'total_assets': len(allocations),
            'max_concentration': round(max_concentration * 100, 1),
            'recommendations': cls._get_diversification_recommendations(allocations, asset_types)
        }
    
    @classmethod
    def _get_diversification_recommendations(cls, allocations: Dict[str, float], asset_types: Dict) -> List[str]:
        """Generate diversification recommendations"""
        recommendations = []
        
        # Check for missing major asset classes
        if 'Acciones' not in asset_types and any(w > 0.1 for w in allocations.values()):
            recommendations.append("Considere agregar exposición a acciones para crecimiento a largo plazo")
        
        if 'Bonos' not in asset_types and any(w > 0.1 for w in allocations.values()):
            recommendations.append("Considere agregar bonos para estabilidad y ingresos")
        
        # Check for over-concentration
        max_weight = max(allocations.values()) if allocations else 0
        if max_weight > 0.6:
            recommendations.append("Portafolio muy concentrado. Considere diversificar más")
        
        # Check for too many small positions
        small_positions = sum(1 for w in allocations.values() if w < 0.05)
        if small_positions > 2:
            recommendations.append("Muchas posiciones pequeñas. Considere consolidar")
        
        return recommendations