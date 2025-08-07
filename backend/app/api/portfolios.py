"""
Portfolios API endpoints - Portfolio management, creation, and performance tracking
"""
from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from flasgger import swag_from
from datetime import datetime

from .. import db
from ..models.user import User
from ..models.risk_profile import RiskProfile
from ..models.portfolio import Portfolio
from ..services.etf_service import ETFService

portfolios_bp = Blueprint('portfolios', __name__)

@portfolios_bp.route('', methods=['GET'])
@jwt_required()
def get_user_portfolios():
    """
    Get all portfolios for current user
    ---
    tags:
      - Portfolios
    responses:
      200:
        description: User portfolios list
    """
    try:
        user_id = get_jwt_identity()
        
        portfolios = Portfolio.query.filter_by(
            user_id=user_id,
            is_active=True
        ).order_by(Portfolio.created_at.desc()).all()
        
        return jsonify({
            'success': True,
            'data': [portfolio.to_dict() for portfolio in portfolios],
            'count': len(portfolios)
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@portfolios_bp.route('/<int:portfolio_id>', methods=['GET'])
@jwt_required()
def get_portfolio(portfolio_id):
    """
    Get specific portfolio by ID
    ---
    tags:
      - Portfolios
    parameters:
      - name: portfolio_id
        in: path
        type: integer
        required: true
    responses:
      200:
        description: Portfolio details
      404:
        description: Portfolio not found
    """
    try:
        user_id = get_jwt_identity()
        
        portfolio = Portfolio.query.filter_by(
            id=portfolio_id,
            user_id=user_id,
            is_active=True
        ).first()
        
        if not portfolio:
            return jsonify({
                'success': False,
                'error': 'Portfolio no encontrado'
            }), 404
        
        return jsonify({
            'success': True,
            'data': portfolio.to_dict(include_performance=True)
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@portfolios_bp.route('', methods=['POST'])
@jwt_required()
def create_portfolio():
    """
    Create new portfolio
    ---
    tags:
      - Portfolios
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            risk_profile_id:
              type: integer
              description: Risk profile ID (optional, uses latest if not provided)
            allocations:
              type: object
              additionalProperties:
                type: number
              description: Custom allocations (optional, uses model if not provided)
            initial_investment:
              type: number
              description: Initial investment amount
    responses:
      201:
        description: Portfolio created successfully
      400:
        description: Invalid data
    """
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        risk_profile_id = data.get('risk_profile_id')
        custom_allocations = data.get('allocations')
        initial_investment = data.get('initial_investment')
        
        # Get risk profile
        if risk_profile_id:
            risk_profile = RiskProfile.query.filter_by(
                id=risk_profile_id,
                user_id=user_id,
                is_active=True
            ).first()
        else:
            # Use latest active risk profile
            risk_profile = RiskProfile.query.filter_by(
                user_id=user_id,
                is_active=True
            ).order_by(RiskProfile.created_at.desc()).first()
        
        if not risk_profile:
            return jsonify({
                'success': False,
                'error': 'Perfil de riesgo no encontrado. Complete el cuestionario primero.'
            }), 400
        
        # Determine allocations
        if custom_allocations:
            # Validate custom allocations
            is_valid, errors = ETFService.validate_allocation(custom_allocations)
            if not is_valid:
                return jsonify({
                    'success': False,
                    'error': 'Asignaciones inválidas',
                    'validation_errors': errors
                }), 400
            allocations = custom_allocations
        else:
            # Use model portfolio
            allocations = Portfolio.MODEL_PORTFOLIOS[risk_profile.risk_bucket].copy()
        
        # Validate initial investment if provided
        if initial_investment is not None:
            if not isinstance(initial_investment, (int, float)) or initial_investment <= 0:
                return jsonify({
                    'success': False,
                    'error': 'Monto de inversión inicial debe ser mayor a 0'
                }), 400
        
        # Deactivate previous portfolios
        previous_portfolios = Portfolio.query.filter_by(
            user_id=user_id,
            is_active=True
        ).all()
        for portfolio in previous_portfolios:
            portfolio.is_active = False
        
        # Create new portfolio
        new_portfolio = Portfolio(
            user_id=user_id,
            risk_profile_id=risk_profile.id,
            allocations=allocations,
            initial_investment=initial_investment
        )
        
        db.session.add(new_portfolio)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Portfolio creado exitosamente',
            'data': new_portfolio.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@portfolios_bp.route('/<int:portfolio_id>', methods=['PUT'])
@jwt_required()
def update_portfolio(portfolio_id):
    """
    Update portfolio allocations
    ---
    tags:
      - Portfolios
    parameters:
      - name: portfolio_id
        in: path
        type: integer
        required: true
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            allocations:
              type: object
              additionalProperties:
                type: number
            initial_investment:
              type: number
    responses:
      200:
        description: Portfolio updated successfully
      404:
        description: Portfolio not found
    """
    try:
        user_id = get_jwt_identity()
        
        portfolio = Portfolio.query.filter_by(
            id=portfolio_id,
            user_id=user_id,
            is_active=True
        ).first()
        
        if not portfolio:
            return jsonify({
                'success': False,
                'error': 'Portfolio no encontrado'
            }), 404
        
        data = request.get_json()
        
        # Update allocations if provided
        if 'allocations' in data:
            new_allocations = data['allocations']
            is_valid, errors = ETFService.validate_allocation(new_allocations)
            if not is_valid:
                return jsonify({
                    'success': False,
                    'error': 'Asignaciones inválidas',
                    'validation_errors': errors
                }), 400
            portfolio.allocations = new_allocations
        
        # Update initial investment if provided
        if 'initial_investment' in data:
            initial_investment = data['initial_investment']
            if initial_investment is not None:
                if not isinstance(initial_investment, (int, float)) or initial_investment <= 0:
                    return jsonify({
                        'success': False,
                        'error': 'Monto de inversión inicial debe ser mayor a 0'
                    }), 400
            portfolio.initial_investment = initial_investment
        
        portfolio.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Portfolio actualizado exitosamente',
            'data': portfolio.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@portfolios_bp.route('/<int:portfolio_id>', methods=['DELETE'])
@jwt_required()
def delete_portfolio(portfolio_id):
    """
    Delete (deactivate) portfolio
    ---
    tags:
      - Portfolios
    parameters:
      - name: portfolio_id
        in: path
        type: integer
        required: true
    responses:
      200:
        description: Portfolio deleted successfully
      404:
        description: Portfolio not found
    """
    try:
        user_id = get_jwt_identity()
        
        portfolio = Portfolio.query.filter_by(
            id=portfolio_id,
            user_id=user_id,
            is_active=True
        ).first()
        
        if not portfolio:
            return jsonify({
                'success': False,
                'error': 'Portfolio no encontrado'
            }), 404
        
        portfolio.is_active = False
        portfolio.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Portfolio eliminado exitosamente'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@portfolios_bp.route('/current', methods=['GET'])
@jwt_required()
def get_current_portfolio():
    """
    Get user's current active portfolio
    ---
    tags:
      - Portfolios
    responses:
      200:
        description: Current portfolio
      404:
        description: No active portfolio found
    """
    try:
        user_id = get_jwt_identity()
        
        portfolio = Portfolio.query.filter_by(
            user_id=user_id,
            is_active=True
        ).order_by(Portfolio.created_at.desc()).first()
        
        if not portfolio:
            return jsonify({
                'success': False,
                'error': 'No hay portfolio activo. Crea uno primero.'
            }), 404
        
        return jsonify({
            'success': True,
            'data': portfolio.to_dict(include_performance=True)
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@portfolios_bp.route('/model/<int:risk_bucket>', methods=['GET'])
def get_model_portfolio(risk_bucket):
    """
    Get model portfolio for risk bucket
    ---
    tags:
      - Portfolios
    parameters:
      - name: risk_bucket
        in: path
        type: integer
        required: true
        minimum: 0
        maximum: 4
        description: Risk bucket (0=Conservative, 4=Aggressive)
    responses:
      200:
        description: Model portfolio
      400:
        description: Invalid risk bucket
    """
    try:
        if risk_bucket not in range(5):
            return jsonify({
                'success': False,
                'error': 'Risk bucket debe estar entre 0 y 4'
            }), 400
        
        model_allocation = Portfolio.MODEL_PORTFOLIOS[risk_bucket].copy()
        risk_label = RiskProfile.RISK_LABELS[risk_bucket]
        
        # Add ETF details
        allocation_breakdown = []
        for ticker, weight in model_allocation.items():
            etf_info = ETFService.get_etf_info(ticker)
            allocation_breakdown.append({
                'ticker': ticker,
                'weight': weight,
                'weight_pct': weight * 100,
                'etf_info': etf_info
            })
        
        return jsonify({
            'success': True,
            'data': {
                'risk_bucket': risk_bucket,
                'risk_label': risk_label,
                'allocations': model_allocation,
                'allocation_breakdown': allocation_breakdown,
                'is_balanced': True,
                'total_allocation': 1.0
            }
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@portfolios_bp.route('/<int:portfolio_id>/rebalance', methods=['GET'])
@jwt_required()
def get_rebalance_suggestions(portfolio_id):
    """
    Get rebalancing suggestions for portfolio
    ---
    tags:
      - Portfolios
    parameters:
      - name: portfolio_id
        in: path
        type: integer
        required: true
    responses:
      200:
        description: Rebalancing suggestions
      404:
        description: Portfolio not found
    """
    try:
        user_id = get_jwt_identity()
        
        portfolio = Portfolio.query.filter_by(
            id=portfolio_id,
            user_id=user_id,
            is_active=True
        ).first()
        
        if not portfolio:
            return jsonify({
                'success': False,
                'error': 'Portfolio no encontrado'
            }), 404
        
        # For now, return placeholder suggestions
        # In production, this would calculate based on current market values
        suggestions = portfolio.calculate_rebalancing_needed()
        
        return jsonify({
            'success': True,
            'data': {
                'portfolio_id': portfolio_id,
                'last_rebalance': portfolio.last_rebalance.isoformat() if portfolio.last_rebalance else None,
                'needs_rebalancing': len(suggestions) > 0,
                'suggestions': suggestions,
                'target_allocations': portfolio.allocations,
                'current_allocations': portfolio.allocations  # Placeholder
            }
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@portfolios_bp.route('/<int:portfolio_id>/performance', methods=['POST'])
@jwt_required()
def update_portfolio_performance(portfolio_id):
    """
    Update portfolio performance metrics
    ---
    tags:
      - Portfolios
    parameters:
      - name: portfolio_id
        in: path
        type: integer
        required: true
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            current_value:
              type: number
            total_return_pct:
              type: number
            annual_return_pct:
              type: number
            volatility_pct:
              type: number
            sharpe_ratio:
              type: number
            max_drawdown_pct:
              type: number
    responses:
      200:
        description: Performance updated successfully
      404:
        description: Portfolio not found
    """
    try:
        user_id = get_jwt_identity()
        
        portfolio = Portfolio.query.filter_by(
            id=portfolio_id,
            user_id=user_id,
            is_active=True
        ).first()
        
        if not portfolio:
            return jsonify({
                'success': False,
                'error': 'Portfolio no encontrado'
            }), 404
        
        data = request.get_json()
        performance_metrics = {
            key: value for key, value in data.items()
            if key in ['current_value', 'total_return_pct', 'annual_return_pct', 
                      'volatility_pct', 'sharpe_ratio', 'max_drawdown_pct']
        }
        
        portfolio.update_performance_metrics(performance_metrics)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Métricas de performance actualizadas',
            'data': portfolio.to_dict(include_performance=True)
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@portfolios_bp.route('/compare', methods=['POST'])
@jwt_required()
def compare_portfolios():
    """
    Compare multiple portfolio allocations
    ---
    tags:
      - Portfolios
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            portfolios:
              type: array
              items:
                type: object
                properties:
                  name:
                    type: string
                  allocations:
                    type: object
                    additionalProperties:
                      type: number
    responses:
      200:
        description: Portfolio comparison
    """
    try:
        data = request.get_json()
        portfolios_to_compare = data.get('portfolios', [])
        
        if not portfolios_to_compare or len(portfolios_to_compare) < 2:
            return jsonify({
                'success': False,
                'error': 'Debe proporcionar al menos 2 portfolios para comparar'
            }), 400
        
        comparison_results = []
        
        for portfolio_data in portfolios_to_compare:
            name = portfolio_data.get('name', 'Portfolio sin nombre')
            allocations = portfolio_data.get('allocations', {})
            
            # Validate allocations
            is_valid, errors = ETFService.validate_allocation(allocations)
            
            # Calculate diversification score
            diversification = ETFService.get_diversification_score(allocations)
            
            comparison_results.append({
                'name': name,
                'allocations': allocations,
                'is_valid': is_valid,
                'validation_errors': errors if not is_valid else [],
                'diversification': diversification,
                'asset_breakdown': diversification['breakdown']
            })
        
        return jsonify({
            'success': True,
            'data': {
                'portfolios': comparison_results,
                'comparison_count': len(comparison_results)
            }
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500