import unittest
import sys
import os

# Agregar el directorio padre al path para importar módulos
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scoring import score_user, bucket_to_label

class TestScoring(unittest.TestCase):
    
    def setUp(self):
        """Configurar datos de prueba"""
        self.sample_answers_conservative = {
            "age": 65,
            "horizon": "< 3 años",
            "income": "< 5 %",
            "knowledge": "Principiante",
            "max_drop": "5 %",
            "reaction": "Vendo todo",
            "liquidity": "Alta",
            "goal": "Proteger capital",
            "inflation": "No me preocupa",
            "digital": "Baja"
        }
        
        self.sample_answers_aggressive = {
            "age": 25,
            "horizon": "> 10 años",
            "income": "> 20 %",
            "knowledge": "Avanzado",
            "max_drop": "> 30 %",
            "reaction": "Compro más",
            "liquidity": "Baja",
            "goal": "Máximo crecimiento",
            "inflation": "Me preocupa mucho",
            "digital": "Alta"
        }
    
    def test_conservative_profile(self):
        """Probar perfil conservador"""
        bucket, score = score_user(self.sample_answers_conservative)
        
        # El perfil conservador debería tener bucket 0 y score bajo
        self.assertEqual(bucket, 0)
        self.assertLess(score, 15)  # Score bajo para perfil conservador
        self.assertEqual(bucket_to_label[bucket], "Conservador")
    
    def test_aggressive_profile(self):
        """Probar perfil agresivo"""
        bucket, score = score_user(self.sample_answers_aggressive)
        
        # El perfil agresivo debería tener bucket alto y score alto
        self.assertGreaterEqual(bucket, 3)  # Bucket 3 o 4
        self.assertGreater(score, 35)  # Score alto para perfil agresivo
        self.assertIn(bucket_to_label[bucket], ["Crecimiento", "Agresivo"])
    
    def test_score_range(self):
        """Probar que el score esté en el rango correcto"""
        bucket, score = score_user(self.sample_answers_conservative)
        
        # El score debe estar entre 0 y 50
        self.assertGreaterEqual(score, 0)
        self.assertLessEqual(score, 50)
        
        # El bucket debe estar entre 0 y 4
        self.assertGreaterEqual(bucket, 0)
        self.assertLessEqual(bucket, 4)
    
    def test_bucket_labels(self):
        """Probar que todos los buckets tengan etiquetas válidas"""
        for bucket in range(5):
            self.assertIn(bucket, bucket_to_label)
            self.assertIsInstance(bucket_to_label[bucket], str)
            self.assertGreater(len(bucket_to_label[bucket]), 0)
    
    def test_missing_answers(self):
        """Probar manejo de respuestas faltantes"""
        incomplete_answers = {
            "age": 30,
            "horizon": "5-10 años"
            # Faltan otras respuestas
        }
        
        # Debería lanzar KeyError o manejar el error graciosamente
        with self.assertRaises(KeyError):
            score_user(incomplete_answers)

if __name__ == '__main__':
    unittest.main()