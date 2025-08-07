"""
Risk Analysis API endpoints - Portfolio risk assessment and profiling
"""
from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from flasgger import swag_from

from .. import db
from ..models.user import User
from ..models.risk_profile import RiskProfile
from ..models.portfolio import Portfolio

analysis_bp = Blueprint('analysis', __name__)

@analysis_bp.route('/risk-profile', methods=['POST'])
@jwt_required()
def create_risk_profile():
    """
    Create or update user risk profile based on questionnaire
    ---
    tags:
      - Analysis
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            answers:
              type: object
              properties:
                age:
                  type: integer
                  minimum: 18
                  maximum: 100
                horizon:
                  type: string
                  enum: ["< 3 años", "3-5 años", "5-10 años", "> 10 años"]
                income:
                  type: string
                  enum: ["< 5 %", "5-10 %", "10-20 %", "> 20 %"]
                knowledge:
                  type: string
                  enum: ["Principiante", "Intermedio", "Avanzado"]
                max_drop:
                  type: string
                  enum: ["5 %", "10 %", "20 %", "30 %", "> 30 %"]
                reaction:
                  type: string
                  enum: ["Vendo todo", "Vendo una parte", "No hago nada", "Compro más"]
                liquidity:
                  type: string
                  enum: ["Alta", "Media", "Baja"]
                goal:
                  type: string
                  enum: ["Proteger capital", "Ingresos regulares", "Crecimiento balanceado", "Máximo crecimiento"]
                inflation:
                  type: string
                  enum: ["No me preocupa", "Me preocupa moderadamente", "Me preocupa mucho"]
                digital:
                  type: string
                  enum: ["Baja", "Media", "Alta"]
    responses:
      200:
        description: Risk profile created successfully
      400:
        description: Invalid questionnaire data
    """
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        answers = data.get('answers', {})
        
        # Validate required fields
        required_fields = [
            'age', 'horizon', 'income', 'knowledge', 'max_drop',
            'reaction', 'liquidity', 'goal', 'inflation', 'digital'
        ]
        
        missing_fields = [field for field in required_fields if field not in answers]
        if missing_fields:
            return jsonify({
                'success': False,
                'error': f'Campos requeridos faltantes: {", ".join(missing_fields)}'
            }), 400
        
        # Validate age range
        age = answers.get('age')
        if not isinstance(age, int) or age < 18 or age > 100:
            return jsonify({
                'success': False,
                'error': 'Edad debe ser un número entero entre 18 y 100'
            }), 400
        
        # Calculate risk profile
        risk_bucket, total_score = RiskProfile.calculate_risk_score(answers)
        
        # Create new risk profile (deactivate previous ones)
        user = User.query.get(user_id)
        if not user:
            return jsonify({
                'success': False,
                'error': 'Usuario no encontrado'
            }), 404
        
        # Deactivate previous risk profiles
        previous_profiles = RiskProfile.query.filter_by(user_id=user_id, is_active=True).all()
        for profile in previous_profiles:
            profile.is_active = False
        
        # Create new risk profile
        new_profile = RiskProfile(
            user_id=user_id,
            questionnaire_answers=answers,
            total_score=total_score,
            risk_bucket=risk_bucket
        )
        
        db.session.add(new_profile)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'data': new_profile.to_dict(),
            'message': 'Perfil de riesgo creado exitosamente'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@analysis_bp.route('/risk-profile', methods=['GET'])
@jwt_required()
def get_current_risk_profile():
    """
    Get current user's risk profile
    ---
    tags:
      - Analysis
    responses:
      200:
        description: Current risk profile
      404:
        description: No risk profile found
    """
    try:
        user_id = get_jwt_identity()
        
        profile = RiskProfile.query.filter_by(
            user_id=user_id, 
            is_active=True
        ).order_by(RiskProfile.created_at.desc()).first()
        
        if not profile:
            return jsonify({
                'success': False,
                'error': 'No se encontró perfil de riesgo activo'
            }), 404
        
        return jsonify({
            'success': True,
            'data': profile.to_dict()
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@analysis_bp.route('/risk-profile/history', methods=['GET'])
@jwt_required()
def get_risk_profile_history():
    """
    Get user's risk profile history
    ---
    tags:
      - Analysis
    responses:
      200:
        description: Risk profile history
    """
    try:
        user_id = get_jwt_identity()
        
        profiles = RiskProfile.query.filter_by(
            user_id=user_id
        ).order_by(RiskProfile.created_at.desc()).all()
        
        return jsonify({
            'success': True,
            'data': [profile.to_dict() for profile in profiles],
            'count': len(profiles)
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@analysis_bp.route('/simulate-score', methods=['POST'])
def simulate_risk_score():
    """
    Simulate risk score without saving (for testing questionnaire)
    ---
    tags:
      - Analysis
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            answers:
              type: object
    responses:
      200:
        description: Simulated risk score
    """
    try:
        data = request.get_json()
        answers = data.get('answers', {})
        
        if not answers:
            return jsonify({
                'success': False,
                'error': 'Debe proporcionar respuestas del cuestionario'
            }), 400
        
        risk_bucket, total_score = RiskProfile.calculate_risk_score(answers)
        risk_label = RiskProfile.RISK_LABELS.get(risk_bucket, 'Desconocido')
        
        # Get model portfolio for this risk level
        model_portfolio = Portfolio.MODEL_PORTFOLIOS.get(risk_bucket, {})
        
        return jsonify({
            'success': True,
            'data': {
                'risk_bucket': risk_bucket,
                'total_score': total_score,
                'risk_label': risk_label,
                'risk_description': f"Perfil {risk_label.lower()} con puntaje {total_score}/50",
                'model_portfolio': model_portfolio,
                'answers': answers
            }
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@analysis_bp.route('/questionnaire/structure', methods=['GET'])
def get_questionnaire_structure():
    """
    Get questionnaire structure and options
    ---
    tags:
      - Analysis
    responses:
      200:
        description: Questionnaire structure
    """
    try:
        structure = {
            'questions': [
                {
                    'key': 'age',
                    'title': '¿Cuál es tu edad?',
                    'type': 'slider',
                    'min': 18,
                    'max': 75,
                    'default': 30,
                    'category': 'demographics'
                },
                {
                    'key': 'horizon',
                    'title': 'Horizonte de inversión',
                    'type': 'select',
                    'options': ["< 3 años", "3-5 años", "5-10 años", "> 10 años"],
                    'category': 'investment'
                },
                {
                    'key': 'income',
                    'title': '% de ingresos para invertir',
                    'type': 'select',
                    'options': ["< 5 %", "5-10 %", "10-20 %", "> 20 %"],
                    'category': 'financial'
                },
                {
                    'key': 'knowledge',
                    'title': 'Conocimiento financiero',
                    'type': 'select',
                    'options': ["Principiante", "Intermedio", "Avanzado"],
                    'category': 'experience'
                },
                {
                    'key': 'max_drop',
                    'title': 'Caída máxima tolerable',
                    'type': 'select',
                    'options': ["5 %", "10 %", "20 %", "30 %", "> 30 %"],
                    'category': 'risk_tolerance'
                },
                {
                    'key': 'reaction',
                    'title': 'Si tu portafolio cae 15%',
                    'type': 'select',
                    'options': ["Vendo todo", "Vendo una parte", "No hago nada", "Compro más"],
                    'category': 'behavior'
                },
                {
                    'key': 'liquidity',
                    'title': 'Necesidad de liquidez',
                    'type': 'select',
                    'options': ["Alta", "Media", "Baja"],
                    'category': 'preferences'
                },
                {
                    'key': 'goal',
                    'title': 'Objetivo principal',
                    'type': 'select',
                    'options': ["Proteger capital", "Ingresos regulares", "Crecimiento balanceado", "Máximo crecimiento"],
                    'category': 'objectives'
                },
                {
                    'key': 'inflation',
                    'title': 'Preocupación por inflación',
                    'type': 'select',
                    'options': ["No me preocupa", "Me preocupa moderadamente", "Me preocupa mucho"],
                    'category': 'concerns'
                },
                {
                    'key': 'digital',
                    'title': 'Confianza en plataformas digitales',
                    'type': 'select',
                    'options': ["Baja", "Media", "Alta"],
                    'category': 'preferences'
                }
            ],
            'risk_levels': [
                {
                    'bucket': 0,
                    'label': 'Conservador',
                    'description': 'Prioriza preservación del capital',
                    'score_range': [0, 12],
                    'color': '#4CAF50'
                },
                {
                    'bucket': 1,
                    'label': 'Moderado', 
                    'description': 'Balance entre seguridad y crecimiento',
                    'score_range': [13, 20],
                    'color': '#2196F3'
                },
                {
                    'bucket': 2,
                    'label': 'Balanceado',
                    'description': 'Distribución equilibrada',
                    'score_range': [21, 28],
                    'color': '#FF9800'
                },
                {
                    'bucket': 3,
                    'label': 'Crecimiento',
                    'description': 'Enfocado en crecimiento largo plazo',
                    'score_range': [29, 36],
                    'color': '#FF5722'
                },
                {
                    'bucket': 4,
                    'label': 'Agresivo',
                    'description': 'Máximo crecimiento, alta volatilidad',
                    'score_range': [37, 50],
                    'color': '#9C27B0'
                }
            ]
        }
        
        return jsonify({
            'success': True,
            'data': structure
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500