from flask import Blueprint, jsonify, request
from ..utils import token_required, admin_required
from ..services import AuthService
from datetime import datetime

api = Blueprint('api', __name__, url_prefix='/api/v1')

@api.route('/health', methods=['GET'])
def health_check():
    """
    Endpoint para verificar el estado de la API
    """
    return jsonify({
        'status': 'ok',
        'timestamp': datetime.utcnow().isoformat()
    })

@api.route('/profile', methods=['GET'])
@token_required
def get_profile(current_user):
    """
    Obtiene el perfil del usuario actual
    """
    return jsonify(current_user)
