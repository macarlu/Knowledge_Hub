from flask import Blueprint
from .main import main
from .api import api
from .calendar import calendar
from .documents import documents
from .links import links

__all__ = ['main', 'api', 'calendar', 'documents', 'links']

# Crear un blueprint para la API principal
api_bp = Blueprint('api', __name__, url_prefix='/api/v1')

# Registrar los blueprints de la API
api_bp.register_blueprint(api, url_prefix='')
api_bp.register_blueprint(calendar, url_prefix='/calendar')
api_bp.register_blueprint(documents, url_prefix='/documents')
api_bp.register_blueprint(links, url_prefix='/links')
