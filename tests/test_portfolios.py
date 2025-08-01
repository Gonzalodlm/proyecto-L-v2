import unittest
import sys
import os

# Agregar el directorio padre al path para importar módulos
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from portfolios import MODEL_PORTFOLIOS

class TestPortfolios(unittest.TestCase):
    
    def test_portfolio_structure(self):
        """Probar la estructura de los portafolios"""
        # Debe haber 5 portafolios (buckets 0-4)
        self.assertEqual(len(MODEL_PORTFOLIOS), 5)
        
        # Cada bucket debe existir
        for bucket in range(5):
            self.assertIn(bucket, MODEL_PORTFOLIOS)
    
    def test_portfolio_weights_sum_to_one(self):
        """Probar que los pesos de cada portafolio sumen 1.0"""
        for bucket, portfolio in MODEL_PORTFOLIOS.items():
            total_weight = sum(portfolio.values())
            self.assertAlmostEqual(total_weight, 1.0, places=2, 
                                 msg=f"Portfolio {bucket} weights sum to {total_weight}, not 1.0")
    
    def test_portfolio_weights_positive(self):
        """Probar que todos los pesos sean positivos"""
        for bucket, portfolio in MODEL_PORTFOLIOS.items():
            for ticker, weight in portfolio.items():
                self.assertGreaterEqual(weight, 0, 
                                      msg=f"Negative weight for {ticker} in portfolio {bucket}")
                self.assertLessEqual(weight, 1, 
                                   msg=f"Weight > 1 for {ticker} in portfolio {bucket}")
    
    def test_conservative_portfolio_characteristics(self):
        """Probar características del portafolio conservador (bucket 0)"""
        conservative = MODEL_PORTFOLIOS[0]
        
        # Debe tener alta asignación a efectivo y bonos
        safe_assets = conservative.get('BIL', 0) + conservative.get('AGG', 0)
        self.assertGreater(safe_assets, 0.6, "Conservative portfolio should have >60% in safe assets")
        
        # Debe tener baja asignación a acciones
        equity_weight = conservative.get('ACWI', 0)
        self.assertLess(equity_weight, 0.3, "Conservative portfolio should have <30% in equities")
    
    def test_aggressive_portfolio_characteristics(self):
        """Probar características del portafolio agresivo (bucket 4)"""
        aggressive = MODEL_PORTFOLIOS[4]
        
        # Debe tener alta asignación a acciones
        equity_weight = aggressive.get('ACWI', 0)
        self.assertGreater(equity_weight, 0.6, "Aggressive portfolio should have >60% in equities")
        
        # No debe tener efectivo
        cash_weight = aggressive.get('BIL', 0)
        self.assertEqual(cash_weight, 0, "Aggressive portfolio should have no cash")
    
    def test_valid_tickers(self):
        """Probar que todos los tickers sean válidos"""
        valid_tickers = ['BIL', 'AGG', 'ACWI', 'VNQ', 'GLD']
        
        for bucket, portfolio in MODEL_PORTFOLIOS.items():
            for ticker in portfolio.keys():
                self.assertIn(ticker, valid_tickers, 
                            f"Invalid ticker {ticker} in portfolio {bucket}")
    
    def test_risk_progression(self):
        """Probar que el riesgo progrese correctamente entre portafolios"""
        # El portafolio conservador debe tener menos acciones que el agresivo
        conservative_equity = MODEL_PORTFOLIOS[0].get('ACWI', 0)
        aggressive_equity = MODEL_PORTFOLIOS[4].get('ACWI', 0)
        
        self.assertLess(conservative_equity, aggressive_equity,
                       "Conservative should have less equity than aggressive")
        
        # El portafolio conservador debe tener más bonos que el agresivo
        conservative_bonds = MODEL_PORTFOLIOS[0].get('AGG', 0)
        aggressive_bonds = MODEL_PORTFOLIOS[4].get('AGG', 0)
        
        self.assertGreater(conservative_bonds, aggressive_bonds,
                          "Conservative should have more bonds than aggressive")

if __name__ == '__main__':
    unittest.main()