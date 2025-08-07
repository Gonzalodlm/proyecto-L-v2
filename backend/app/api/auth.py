"""
Authentication API endpoints - User registration, login, token management
"""
from datetime import datetime, timedelta
from flask import Blueprint, jsonify, request
from flask_jwt_extended import (
    jwt_required, create_access_token, create_refresh_token,
    get_jwt_identity, get_jwt
)
from flasgger import swag_from
import re

from .. import db, jwt
from ..models.user import User

auth_bp = Blueprint('auth', __name__)

# Token blacklist (in production use Redis)
blacklisted_tokens = set()

@jwt.token_in_blocklist_loader
def check_if_token_revoked(jwt_header, jwt_payload):
    """Check if JWT token is blacklisted"""
    return jwt_payload['jti'] in blacklisted_tokens

def validate_email(email):
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_password(password):
    """Validate password strength"""
    if len(password) < 8:
        return False, "La contraseña debe tener al menos 8 caracteres"
    
    if not re.search(r'[A-Z]', password):
        return False, "La contraseña debe contener al menos una mayúscula"
    
    if not re.search(r'[a-z]', password):
        return False, "La contraseña debe contener al menos una minúscula"
    
    if not re.search(r'\d', password):
        return False, "La contraseña debe contener al menos un número"
    
    return True, "Contraseña válida"

@auth_bp.route('/register', methods=['POST'])
def register():
    """
    Register new user
    ---
    tags:
      - Authentication
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          required:
            - email
            - password
          properties:
            email:
              type: string
              format: email
              example: "user@example.com"
            password:
              type: string
              minLength: 8
              example: "SecurePass123"
            first_name:
              type: string
              example: "Juan"
            last_name:
              type: string
              example: "Pérez"
    responses:
      201:
        description: User registered successfully
      400:
        description: Invalid input data
      409:
        description: Email already exists
    """
    try:
        data = request.get_json()
        
        # Validate required fields
        email = data.get('email', '').strip().lower()
        password = data.get('password', '')
        first_name = data.get('first_name', '').strip()
        last_name = data.get('last_name', '').strip()
        
        if not email or not password:
            return jsonify({
                'success': False,
                'error': 'Email y contraseña son requeridos'
            }), 400
        
        # Validate email format
        if not validate_email(email):
            return jsonify({
                'success': False,
                'error': 'Formato de email inválido'
            }), 400
        
        # Validate password strength
        is_valid_password, password_message = validate_password(password)
        if not is_valid_password:
            return jsonify({
                'success': False,
                'error': password_message
            }), 400
        
        # Check if user already exists
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            return jsonify({
                'success': False,
                'error': 'El email ya está registrado'
            }), 409
        
        # Create new user
        new_user = User(
            email=email,
            password=password,
            first_name=first_name if first_name else None,
            last_name=last_name if last_name else None
        )
        
        db.session.add(new_user)
        db.session.commit()
        
        # Create tokens
        access_token = create_access_token(identity=new_user.id)
        refresh_token = create_refresh_token(identity=new_user.id)
        
        return jsonify({
            'success': True,
            'message': 'Usuario registrado exitosamente',
            'data': {
                'user': new_user.to_dict(),
                'access_token': access_token,
                'refresh_token': refresh_token
            }
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@auth_bp.route('/login', methods=['POST'])
def login():
    """
    User login
    ---
    tags:
      - Authentication
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          required:
            - email
            - password
          properties:
            email:
              type: string
              format: email
            password:
              type: string
    responses:
      200:
        description: Login successful
      401:
        description: Invalid credentials
    """
    try:
        data = request.get_json()
        
        email = data.get('email', '').strip().lower()
        password = data.get('password', '')
        
        if not email or not password:
            return jsonify({
                'success': False,
                'error': 'Email y contraseña son requeridos'
            }), 400
        
        # Find user
        user = User.query.filter_by(email=email).first()
        
        # Check credentials
        if not user or not user.check_password(password):
            return jsonify({
                'success': False,
                'error': 'Credenciales inválidas'
            }), 401
        
        # Check if user is active
        if not user.is_active:
            return jsonify({
                'success': False,
                'error': 'Cuenta desactivada. Contacte soporte.'
            }), 401
        
        # Create tokens
        access_token = create_access_token(identity=user.id)
        refresh_token = create_refresh_token(identity=user.id)
        
        return jsonify({
            'success': True,
            'message': 'Login exitoso',
            'data': {
                'user': user.to_dict(include_sensitive=True),
                'access_token': access_token,
                'refresh_token': refresh_token
            }
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@auth_bp.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    """
    Refresh access token
    ---
    tags:
      - Authentication
    responses:
      200:
        description: Token refreshed successfully
    """
    try:
        user_id = get_jwt_identity()
        
        # Verify user still exists and is active
        user = User.query.get(user_id)
        if not user or not user.is_active:
            return jsonify({
                'success': False,
                'error': 'Usuario no válido'
            }), 401
        
        # Create new access token
        new_access_token = create_access_token(identity=user_id)
        
        return jsonify({
            'success': True,
            'data': {
                'access_token': new_access_token
            }
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@auth_bp.route('/logout', methods=['DELETE'])
@jwt_required()
def logout():
    """
    Logout user (blacklist token)
    ---
    tags:
      - Authentication
    responses:
      200:
        description: Logout successful
    """
    try:
        jti = get_jwt()['jti']
        blacklisted_tokens.add(jti)
        
        return jsonify({
            'success': True,
            'message': 'Logout exitoso'
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@auth_bp.route('/profile', methods=['GET'])
@jwt_required()
def get_profile():
    """
    Get current user profile
    ---
    tags:
      - Authentication
    responses:
      200:
        description: User profile
      404:
        description: User not found
    """
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if not user:
            return jsonify({
                'success': False,
                'error': 'Usuario no encontrado'
            }), 404
        
        return jsonify({
            'success': True,
            'data': user.to_dict(include_sensitive=True)
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@auth_bp.route('/profile', methods=['PUT'])
@jwt_required()
def update_profile():
    """
    Update user profile
    ---
    tags:
      - Authentication
    parameters:
      - name: body
        in: body
        schema:
          type: object
          properties:
            first_name:
              type: string
            last_name:
              type: string
    responses:
      200:
        description: Profile updated successfully
    """
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if not user:
            return jsonify({
                'success': False,
                'error': 'Usuario no encontrado'
            }), 404
        
        data = request.get_json()
        
        # Update allowed fields
        if 'first_name' in data:
            user.first_name = data['first_name'].strip() if data['first_name'] else None
            
        if 'last_name' in data:
            user.last_name = data['last_name'].strip() if data['last_name'] else None
        
        user.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Perfil actualizado exitosamente',
            'data': user.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@auth_bp.route('/change-password', methods=['POST'])
@jwt_required()
def change_password():
    """
    Change user password
    ---
    tags:
      - Authentication
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          required:
            - current_password
            - new_password
          properties:
            current_password:
              type: string
            new_password:
              type: string
              minLength: 8
    responses:
      200:
        description: Password changed successfully
      400:
        description: Invalid current password
    """
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if not user:
            return jsonify({
                'success': False,
                'error': 'Usuario no encontrado'
            }), 404
        
        data = request.get_json()
        current_password = data.get('current_password', '')
        new_password = data.get('new_password', '')
        
        if not current_password or not new_password:
            return jsonify({
                'success': False,
                'error': 'Contraseña actual y nueva son requeridas'
            }), 400
        
        # Verify current password
        if not user.check_password(current_password):
            return jsonify({
                'success': False,
                'error': 'Contraseña actual incorrecta'
            }), 400
        
        # Validate new password
        is_valid_password, password_message = validate_password(new_password)
        if not is_valid_password:
            return jsonify({
                'success': False,
                'error': password_message
            }), 400
        
        # Update password
        user.set_password(new_password)
        user.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Contraseña cambiada exitosamente'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@auth_bp.route('/verify-token', methods=['GET'])
@jwt_required()
def verify_token():
    """
    Verify if token is valid
    ---
    tags:
      - Authentication
    responses:
      200:
        description: Token is valid
    """
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if not user or not user.is_active:
            return jsonify({
                'success': False,
                'error': 'Token inválido'
            }), 401
        
        return jsonify({
            'success': True,
            'message': 'Token válido',
            'data': {
                'user_id': user_id,
                'email': user.email
            }
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500