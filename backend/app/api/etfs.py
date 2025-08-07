"""
ETFs API endpoints - Information about supported ETFs
"""
from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from flasgger import swag_from

from app.services.etf_service import ETFService

etfs_bp = Blueprint('etfs', __name__)

@etfs_bp.route('', methods=['GET'])
def get_all_etfs():
    """
    Get all supported ETFs information
    ---
    tags:
      - ETFs
    responses:
      200:
        description: List of all supported ETFs
        schema:
          type: object
          properties:
            success:
              type: boolean
            data:
              type: object
              additionalProperties:
                type: object
    """
    try:
        etfs = ETFService.get_all_etfs()
        return jsonify({
            'success': True,
            'data': etfs,
            'count': len(etfs)
        }), 200
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@etfs_bp.route('/<ticker>', methods=['GET'])  
def get_etf_info(ticker):
    """
    Get specific ETF information
    ---
    tags:
      - ETFs
    parameters:
      - name: ticker
        in: path
        type: string
        required: true
        description: ETF ticker symbol
    responses:
      200:
        description: ETF information
      404:
        description: ETF not found
    """
    try:
        etf_info = ETFService.get_etf_info(ticker)
        
        if not etf_info:
            return jsonify({
                'success': False,
                'error': f'ETF {ticker} no encontrado'
            }), 404
        
        return jsonify({
            'success': True,
            'data': etf_info
        }), 200
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@etfs_bp.route('/filter/type/<etf_type>', methods=['GET'])
def get_etfs_by_type(etf_type):
    """
    Get ETFs filtered by type
    ---
    tags:
      - ETFs
    parameters:
      - name: etf_type
        in: path
        type: string
        required: true
        description: ETF type (e.g., Acciones, Bonos, REITs)
    responses:
      200:
        description: Filtered ETFs list
    """
    try:
        etfs = ETFService.get_etfs_by_type(etf_type)
        return jsonify({
            'success': True,
            'data': etfs,
            'count': len(etfs),
            'filter': {'type': etf_type}
        }), 200
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@etfs_bp.route('/filter/risk/<risk_level>', methods=['GET']) 
def get_etfs_by_risk(risk_level):
    """
    Get ETFs filtered by risk level
    ---
    tags:
      - ETFs
    parameters:
      - name: risk_level
        in: path
        type: string
        required: true
        description: Risk level (e.g., Bajo, Medio, Alto)
    responses:
      200:
        description: Filtered ETFs list
    """
    try:
        etfs = ETFService.get_etfs_by_risk(risk_level)
        return jsonify({
            'success': True,
            'data': etfs,
            'count': len(etfs),
            'filter': {'risk': risk_level}
        }), 200
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@etfs_bp.route('/validate', methods=['POST'])
@jwt_required()
def validate_allocation():
    """
    Validate portfolio allocation
    ---
    tags:
      - ETFs  
    parameters:
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
              example:
                BIL: 0.20
                AGG: 0.30
                ACWI: 0.40
                VNQ: 0.10
    responses:
      200:
        description: Validation result
      400:
        description: Invalid allocation
    """
    try:
        data = request.get_json()
        allocations = data.get('allocations', {})
        
        if not allocations:
            return jsonify({
                'success': False,
                'error': 'Debe proporcionar asignaciones de portafolio'
            }), 400
        
        is_valid, errors = ETFService.validate_allocation(allocations)
        
        response_data = {
            'success': is_valid,
            'is_valid': is_valid,
            'allocations': allocations,
            'total_allocation': sum(allocations.values()),
            'total_allocation_pct': sum(allocations.values()) * 100
        }
        
        if not is_valid:
            response_data['errors'] = errors
        else:
            # Add diversification analysis if valid
            diversification = ETFService.get_diversification_score(allocations)
            response_data['diversification'] = diversification
        
        status_code = 200 if is_valid else 400
        return jsonify(response_data), status_code
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@etfs_bp.route('/diversification', methods=['POST'])
@jwt_required()
def analyze_diversification():
    """
    Analyze portfolio diversification
    ---
    tags:
      - ETFs
    parameters:
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
    responses:
      200:
        description: Diversification analysis
    """
    try:
        data = request.get_json()
        allocations = data.get('allocations', {})
        
        if not allocations:
            return jsonify({
                'success': False,
                'error': 'Debe proporcionar asignaciones de portafolio'
            }), 400
        
        # Validate first
        is_valid, errors = ETFService.validate_allocation(allocations)
        if not is_valid:
            return jsonify({
                'success': False,
                'error': 'Asignación de portafolio inválida',
                'validation_errors': errors
            }), 400
        
        # Calculate diversification
        diversification = ETFService.get_diversification_score(allocations)
        
        return jsonify({
            'success': True,
            'data': diversification
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@etfs_bp.route('/tickers', methods=['GET'])
def get_supported_tickers():
    """
    Get list of supported ETF tickers
    ---
    tags:
      - ETFs
    responses:
      200:
        description: List of supported tickers
    """
    try:
        tickers = ETFService.get_supported_tickers()
        return jsonify({
            'success': True,
            'data': tickers,
            'count': len(tickers)
        }), 200
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500