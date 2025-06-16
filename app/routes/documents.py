from flask import Blueprint, jsonify, request
from werkzeug.utils import secure_filename
from ..utils import token_required, allowed_file
from ..services import DocumentsService

documents = Blueprint('documents', __name__, url_prefix='/api/v1/documents')

@documents.route('/upload', methods=['POST'])
@token_required
def upload_document(current_user):
    """
    Sube un nuevo documento
    """
    if 'file' not in request.files:
        return jsonify({'error': 'No se proporcionó archivo'}), 400
        
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No se seleccionó archivo'}), 400
        
    if file and allowed_file(file.filename):
        try:
            document = documents_service.upload_document(
                file=file,
                title=request.form.get('title', file.filename),
                description=request.form.get('description', ''),
                tags=request.form.getlist('tags'),
                categories=request.form.getlist('categories'),
                user_id=current_user['_id']
            )
            return jsonify(document), 201
        except ValueError as e:
            return jsonify({'error': str(e)}), 400
    
    return jsonify({'error': 'Tipo de archivo no permitido'}), 400

@documents.route('/<document_id>', methods=['GET'])
@token_required
def get_document(current_user, document_id):
    """
    Obtiene un documento
    """
    document = documents_service.get_document_by_id(document_id, current_user['_id'])
    if document:
        return jsonify(document)
    return jsonify({'error': 'Documento no encontrado'}), 404

@documents.route('/<document_id>/versions', methods=['GET'])
@token_required
def get_document_versions(current_user, document_id):
    """
    Obtiene todas las versiones de un documento
    """
    versions = documents_service.get_document_versions(document_id, current_user['_id'])
    return jsonify(versions)

@documents.route('/<document_id>/versions', methods=['POST'])
@token_required
def create_document_version(current_user, document_id):
    """
    Crea una nueva versión de un documento
    """
    if 'file' not in request.files:
        return jsonify({'error': 'No se proporcionó archivo'}), 400
        
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No se seleccionó archivo'}), 400
        
    if file and allowed_file(file.filename):
        try:
            version = documents_service.create_new_version(
                document_id=document_id,
                file=file,
                changes=request.form.get('changes', 'Nueva versión'),
                user_id=current_user['_id']
            )
            return jsonify(version), 201
        except ValueError as e:
            return jsonify({'error': str(e)}), 400
    
    return jsonify({'error': 'Tipo de archivo no permitido'}), 400

@documents.route('/search', methods=['GET'])
@token_required
def search_documents(current_user):
    """
    Busca documentos
    """
    query = request.args.get('q', '')
    documents = documents_service.search_documents(query, current_user['_id'])
    return jsonify(documents)

@documents.route('/<document_id>', methods=['DELETE'])
@token_required
def delete_document(current_user, document_id):
    """
    Elimina un documento
    """
    try:
        if documents_service.delete_document(document_id, current_user['_id']):
            return '', 204
        return jsonify({'error': 'Documento no encontrado'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 400
