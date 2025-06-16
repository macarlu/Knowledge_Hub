from datetime import datetime
from typing import Optional, List, Dict, Any
from bson.objectid import ObjectId
from pymongo.errors import DuplicateKeyError
import os
from werkzeug.utils import secure_filename
from ..models.document import Document, DocumentVersion
from .utils import allowed_file, get_file_extension, generate_filename, get_file_size

class DocumentsService:
    """
    Servicio que maneja toda la lógica relacionada con documentos
    """
    
    def __init__(self, db, upload_folder):
        """
        Inicializa el servicio con la conexión a la base de datos y la carpeta de uploads
        Args:
            db: Conexión a MongoDB
            upload_folder: Ruta de la carpeta de uploads
        """
        self.db = db
        self.upload_folder = upload_folder
        self.documents = self.db['documents']
        self.versions = self.db['document_versions']
        
        # Crear índices únicos
        self.documents.create_index([('file_name', 1), ('user_id', 1)], unique=True)
        self.documents.create_index([('title', 1), ('user_id', 1)], unique=True)

    def upload_document(self, file, title: str, description: str, 
                       tags: List[str], categories: List[str], user_id: str) -> Dict:
        """
        Sube un nuevo documento
        
        Args:
            file: Archivo a subir
            title: Título del documento
            description: Descripción del documento
            tags: Lista de etiquetas
            categories: Lista de categorías
            user_id: ID del usuario
            
        Returns:
            Diccionario con los datos del documento subido
            
        Raises:
            ValueError: Si el archivo no es válido o ya existe un documento con el mismo nombre
        """
        # Validar archivo
        if not allowed_file(file.filename):
            raise ValueError('Tipo de archivo no permitido')
            
        # Generar nombre seguro para el archivo
        filename = secure_filename(file.filename)
        file_path = os.path.join(self.upload_folder, filename)
        
        # Guardar archivo
        file.save(file_path)
        
        # Crear documento
        document = {
            'title': title,
            'description': description,
            'file_name': filename,
            'file_path': file_path,
            'file_type': file.content_type,
            'size': os.path.getsize(file_path),
            'tags': tags,
            'categories': categories,
            'version': 1,
            'user_id': user_id,
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow()
        }
        
        try:
            result = self.documents.insert_one(document)
            document['_id'] = str(result.inserted_id)
            
            # Crear versión inicial
            version = {
                'document_id': str(result.inserted_id),
                'file_path': file_path,
                'version_number': 1,
                'changes': 'Versión inicial',
                'user_id': user_id,
                'created_at': datetime.utcnow()
            }
            self.versions.insert_one(version)
            
            return document
            
        except DuplicateKeyError:
            raise ValueError('Ya existe un documento con este nombre o título')

    def get_documents(self, user_id: str, tag: Optional[str] = None, 
                     category: Optional[str] = None) -> List[Dict]:
        """
        Obtiene los documentos de un usuario
        
        Args:
            user_id: ID del usuario
            tag: Etiqueta para filtrar (opcional)
            category: Categoría para filtrar (opcional)
            
        Returns:
            Lista de documentos
        """
        query = {'user_id': user_id}
        if tag:
            query['tags'] = tag
        if category:
            query['categories'] = category
            
        docs = self.documents.find(query)
        return [{**doc, '_id': str(doc['_id'])} for doc in docs]

    def get_document_versions(self, document_id: str, user_id: str) -> List[Dict]:
        """
        Obtiene todas las versiones de un documento
        
        Args:
            document_id: ID del documento
            user_id: ID del usuario
            
        Returns:
            Lista de versiones del documento
        """
        versions = self.versions.find(
            {'document_id': document_id, 'user_id': user_id}
        ).sort('version_number', -1)
        
        return [{**version, '_id': str(version['_id'])} for version in versions]

    def create_new_version(self, document_id: str, file, changes: str, user_id: str) -> Dict:
        """
        Crea una nueva versión de un documento
        
        Args:
            document_id: ID del documento
            file: Nuevo archivo
            changes: Descripción de los cambios
            user_id: ID del usuario
            
        Returns:
            Diccionario con los datos de la nueva versión
            
        Raises:
            ValueError: Si el documento no existe o el archivo no es válido
        """
        # Validar archivo
        if not allowed_file(file.filename):
            raise ValueError('Tipo de archivo no permitido')
            
        # Generar nombre seguro para el archivo
        filename = secure_filename(file.filename)
        file_path = os.path.join(self.upload_folder, filename)
        
        # Guardar archivo
        file.save(file_path)
        
        # Obtener el documento original
        document = self.documents.find_one({'_id': ObjectId(document_id), 'user_id': user_id})
        if not document:
            raise ValueError('Documento no encontrado o no pertenece al usuario')
            
        # Actualizar documento
        new_version = document['version'] + 1
        self.documents.update_one(
            {'_id': ObjectId(document_id)},
            {
                '$set': {
                    'file_name': filename,
                    'file_path': file_path,
                    'file_type': file.content_type,
                    'size': os.path.getsize(file_path),
                    'version': new_version,
                    'updated_at': datetime.utcnow()
                }
            }
        )
        
        # Crear nueva versión
        version = {
            'document_id': document_id,
            'file_path': file_path,
            'version_number': new_version,
            'changes': changes,
            'user_id': user_id,
            'created_at': datetime.utcnow()
        }
        
        self.versions.insert_one(version)
        return version

    def delete_document(self, document_id: str, user_id: str) -> bool:
        """
        Elimina un documento y todas sus versiones
        
        Args:
            document_id: ID del documento
            user_id: ID del usuario
            
        Returns:
            True si el documento fue eliminado, False si no
        """
        # Eliminar documento
        doc_result = self.documents.delete_one({'_id': ObjectId(document_id), 'user_id': user_id})
        
        # Eliminar todas las versiones
        version_result = self.versions.delete_many({'document_id': document_id, 'user_id': user_id})
        
        return doc_result.deleted_count > 0 and version_result.deleted_count > 0

    def get_document_by_id(self, document_id: str, user_id: str) -> Optional[Dict]:
        """
        Obtiene un documento por su ID
        
        Args:
            document_id: ID del documento
            user_id: ID del usuario
            
        Returns:
            Documento si existe y pertenece al usuario, None si no
        """
        document = self.documents.find_one({'_id': ObjectId(document_id), 'user_id': user_id})
        if document:
            return {**document, '_id': str(document['_id'])}
        return None

    def search_documents(self, query: str, user_id: str) -> List[Dict]:
        """
        Busca documentos por título, descripción o tags
        
        Args:
            query: Término de búsqueda
            user_id: ID del usuario
            
        Returns:
            Lista de documentos que coinciden con la búsqueda
        """
        # Buscar en título, descripción y tags
        docs = self.documents.find({
            'user_id': user_id,
            '$or': [
                {'title': {'$regex': query, '$options': 'i'}},
                {'description': {'$regex': query, '$options': 'i'}},
                {'tags': {'$regex': query, '$options': 'i'}}
            ]
        })
        
        return [{**doc, '_id': str(doc['_id'])} for doc in docs]
