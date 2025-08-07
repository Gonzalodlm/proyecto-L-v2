"""
Risk Profile model for storing user risk assessment results
"""
from datetime import datetime
from sqlalchemy.dialects.postgresql import JSON
from .. import db

class RiskProfile(db.Model):
    __tablename__ = 'risk_profiles'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    
    # Risk assessment data
    questionnaire_answers = db.Column(JSON, nullable=False)  # Store all answers
    total_score = db.Column(db.Integer, nullable=False)
    risk_bucket = db.Column(db.Integer, nullable=False)  # 0-4 (Conservative to Aggressive)
    risk_label = db.Column(db.String(20), nullable=False)  # Human-readable label
    
    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    
    # Relationships  
    portfolios = db.relationship('Portfolio', backref='risk_profile', lazy=True)
    
    # Risk bucket to label mapping
    RISK_LABELS = {
        0: "Conservador",
        1: "Moderado", 
        2: "Balanceado",
        3: "Crecimiento",
        4: "Agresivo"
    }
    
    def __init__(self, user_id, questionnaire_answers, total_score, risk_bucket):
        self.user_id = user_id
        self.questionnaire_answers = questionnaire_answers
        self.total_score = total_score
        self.risk_bucket = risk_bucket
        self.risk_label = self.RISK_LABELS[risk_bucket]
    
    @classmethod
    def calculate_risk_score(cls, answers):
        """
        Calculate risk score from questionnaire answers
        Returns (bucket, total_score)
        """
        score = 0
        
        # Age scoring (more young, more risk)
        age = answers.get('age', 30)
        if age < 30:
            score += 5
        elif age < 45:
            score += 4  
        elif age < 60:
            score += 2
        else:
            score += 0
            
        # Investment horizon
        horizon_scores = {"< 3 años": 0, "3-5 años": 2, "5-10 años": 4, "> 10 años": 5}
        score += horizon_scores.get(answers.get('horizon'), 0)
        
        # Income percentage for investing
        income_scores = {"< 5 %": 0, "5-10 %": 1, "10-20 %": 3, "> 20 %": 4}
        score += income_scores.get(answers.get('income'), 0)
        
        # Financial knowledge
        knowledge_scores = {"Principiante": 0, "Intermedio": 2, "Avanzado": 4}
        score += knowledge_scores.get(answers.get('knowledge'), 0)
        
        # Maximum acceptable loss
        loss_scores = {"5 %": 0, "10 %": 1, "20 %": 3, "30 %": 4, "> 30 %": 5}
        score += loss_scores.get(answers.get('max_drop'), 0)
        
        # Reaction to portfolio drop
        reaction_scores = {
            "Vendo todo": 0,
            "Vendo una parte": 1, 
            "No hago nada": 3,
            "Compro más": 5
        }
        score += reaction_scores.get(answers.get('reaction'), 0)
        
        # Liquidity needs
        liquidity_scores = {"Alta": 0, "Media": 2, "Baja": 4}
        score += liquidity_scores.get(answers.get('liquidity'), 0)
        
        # Investment goal
        goal_scores = {
            "Proteger capital": 0,
            "Ingresos regulares": 2,
            "Crecimiento balanceado": 3, 
            "Máximo crecimiento": 5
        }
        score += goal_scores.get(answers.get('goal'), 0)
        
        # Inflation concern
        inflation_scores = {
            "No me preocupa": 0,
            "Me preocupa moderadamente": 2,
            "Me preocupa mucho": 3
        }
        score += inflation_scores.get(answers.get('inflation'), 0)
        
        # Digital platform trust
        digital_scores = {"Baja": 0, "Media": 1, "Alta": 2}
        score += digital_scores.get(answers.get('digital'), 0)
        
        # Convert score to bucket
        if score <= 12:
            bucket = 0  # Conservative
        elif score <= 20:
            bucket = 1  # Moderate
        elif score <= 28:
            bucket = 2  # Balanced
        elif score <= 36:
            bucket = 3  # Growth
        else:
            bucket = 4  # Aggressive
            
        return bucket, score
    
    @property
    def risk_description(self):
        """Get detailed description of risk profile"""
        descriptions = {
            0: "Perfil conservador que prioriza la preservación del capital por encima del crecimiento.",
            1: "Perfil moderado que busca un balance entre seguridad y crecimiento modesto.",
            2: "Perfil balanceado con distribución equilibrada entre riesgo y retorno.", 
            3: "Perfil de crecimiento enfocado en maximizar retornos a largo plazo.",
            4: "Perfil agresivo que busca máximo crecimiento tolerando alta volatilidad."
        }
        return descriptions.get(self.risk_bucket, "")
    
    def to_dict(self):
        """Convert risk profile to dictionary"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'questionnaire_answers': self.questionnaire_answers,
            'total_score': self.total_score,
            'risk_bucket': self.risk_bucket,
            'risk_label': self.risk_label,
            'risk_description': self.risk_description,
            'created_at': self.created_at.isoformat(),
            'is_active': self.is_active
        }
    
    def __repr__(self):
        return f'<RiskProfile user_id={self.user_id} bucket={self.risk_bucket} score={self.total_score}>'