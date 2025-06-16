from flask import Blueprint, jsonify, request
from ..utils import token_required
from ..services import LinksService

links = Blueprint('links', __name__, url_prefix='/api/v1/links')

@links.route('/categories', methods=['POST'])
@token_required
def create_category(current_user):
    """
    Crea una nueva categoría de enlaces
    """
    data = request.get_json()
    try:
        category = links_service.create_category(
            name=data['name'],
            description=data['description'],
            user_id=current_user['_id']
        )
        return jsonify(category), 201
    except ValueError as e:
        return jsonify({'error': str(e)}), 400

@links.route('/categories', methods=['GET'])
@token_required
def get_categories(current_user):
    """
    Obtiene todas las categorías del usuario
    """
    categories = links_service.get_categories(current_user['_id'])
    return jsonify(categories)

@links.route('/add', methods=['POST'])
@token_required
def add_link(current_user):
    """
    Añade un nuevo enlace
    """
    data = request.get_json()
    try:
        link = links_service.add_link(
            url=data['url'],
            title=data.get('title', ''),
            description=data.get('description', ''),
            category=data['category'],
            tags=data.get('tags', []),
            user_id=current_user['_id']
        )
        return jsonify(link), 201
    except ValueError as e:
        return jsonify({'error': str(e)}), 400

@links.route('/<link_id>/visit', methods=['POST'])
@token_required
def increment_visits(current_user, link_id):
    """
    Incrementa el contador de visitas de un enlace
    """
    try:
        if links_service.increment_visits(link_id, current_user['_id']):
            return '', 204
        return jsonify({'error': 'Enlace no encontrado'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@links.route('/<link_id>', methods=['PUT'])
@token_required
def update_link(current_user, link_id):
    """
    Actualiza un enlace
    """
    data = request.get_json()
    try:
        link = links_service.update_link(
            link_id=link_id,
            user_id=current_user['_id'],
            title=data.get('title'),
            description=data.get('description'),
            category=data.get('category'),
            tags=data.get('tags'),
            rating=data.get('rating')
        )
        return jsonify(link)
    except ValueError as e:
        return jsonify({'error': str(e)}), 400

@links.route('/search', methods=['GET'])
@token_required
def search_links(current_user):
    """
    Busca enlaces
    """
    query = request.args.get('q', '')
    links = links_service.search_links(query, current_user['_id'])
    return jsonify(links)

@links.route('/popular', methods=['GET'])
@token_required
def get_popular_links(current_user):
    """
    Obtiene los enlaces más populares
    """
    limit = request.args.get('limit', 10, type=int)
    links = links_service.get_popular_links(current_user['_id'], limit)
    return jsonify(links)

@links.route('/<link_id>', methods=['DELETE'])
@token_required
def delete_link(current_user, link_id):
    """
    Elimina un enlace
    """
    try:
        if links_service.delete_link(link_id, current_user['_id']):
            return '', 204
        return jsonify({'error': 'Enlace no encontrado'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 400
