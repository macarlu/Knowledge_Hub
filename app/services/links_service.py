from datetime import datetime
from typing import Optional, List, Dict, Any
from bson.objectid import ObjectId
from pymongo.errors import DuplicateKeyError
import requests
from bs4 import BeautifulSoup
from ..models.link import Link, LinkCategory
from .utils import validate_url

class LinksService:
    """
    Servicio que maneja toda la lógica relacionada con enlaces
    """
    
    def __init__(self, db):
        """
        Inicializa el servicio con la conexión a la base de datos
        Args:
            db: Conexión a MongoDB
        """
        self.db = db
        self.links = self.db['links']
        self.categories = self.db['link_categories']
        
        # Crear índices únicos
        self.links.create_index([('url', 1), ('user_id', 1)], unique=True)
        self.categories.create_index([('name', 1), ('user_id', 1)], unique=True)

    def create_category(self, name: str, description: str, user_id: str) -> Dict:
        """
        Crea una nueva categoría de enlaces
        
        Args:
            name: Nombre de la categoría
            description: Descripción de la categoría
            user_id: ID del usuario
            
        Returns:
            Diccionario con los datos de la categoría creada
            
        Raises:
            ValueError: Si ya existe una categoría con ese nombre
        """
        try:
            category = {
                'name': name,
                'description': description,
                'user_id': user_id,
                'created_at': datetime.utcnow()
            }
            result = self.categories.insert_one(category)
            category['_id'] = str(result.inserted_id)
            return category
            
        except DuplicateKeyError:
            raise ValueError('Ya existe una categoría con este nombre')

    def add_link(self, url: str, title: str, description: str, 
                category: str, tags: List[str], user_id: str) -> Dict:
        """
        Añade un nuevo enlace
        
        Args:
            url: URL del enlace
            title: Título del enlace
            description: Descripción del enlace
            category: Categoría del enlace
            tags: Lista de etiquetas
            user_id: ID del usuario
            
        Returns:
            Diccionario con los datos del enlace añadido
            
        Raises:
            ValueError: Si la URL no es válida o ya existe un enlace con esa URL
        """
        # Validar URL
        if not validate_url(url):
            raise ValueError('URL no válida')
            
        # Verificar si la categoría existe
        category_doc = self.categories.find_one(
            {'name': category, 'user_id': user_id}
        )
        if not category_doc:
            raise ValueError('Categoría no encontrada')
            
        try:
            # Intentar obtener información adicional de la URL
            try:
                response = requests.get(url)
                soup = BeautifulSoup(response.text, 'html.parser')
                if not title:
                    title = soup.title.string if soup.title else url
                if not description:
                    meta_description = soup.find('meta', attrs={'name': 'description'})
                    description = meta_description['content'] if meta_description else ''
            except:
                pass  # Si falla, usamos los valores proporcionados
                
            link = {
                'url': url,
                'title': title,
                'description': description,
                'category': category,
                'tags': tags,
                'rating': 0,
                'visits': 0,
                'user_id': user_id,
                'created_at': datetime.utcnow(),
                'updated_at': datetime.utcnow()
            }
            
            result = self.links.insert_one(link)
            link['_id'] = str(result.inserted_id)
            return link
            
        except DuplicateKeyError:
            raise ValueError('Ya existe un enlace con esta URL')

    def get_links(self, user_id: str, category: Optional[str] = None, 
                 tag: Optional[str] = None, min_rating: Optional[int] = None) -> List[Dict]:
        """
        Obtiene los enlaces de un usuario
        
        Args:
            user_id: ID del usuario
            category: Categoría para filtrar (opcional)
            tag: Etiqueta para filtrar (opcional)
            min_rating: Calificación mínima (opcional)
            
        Returns:
            Lista de enlaces
        """
        query = {'user_id': user_id}
        if category:
            query['category'] = category
        if tag:
            query['tags'] = tag
        if min_rating is not None:
            query['rating'] = {'$gte': min_rating}
            
        links = self.links.find(query)
        return [{**link, '_id': str(link['_id'])} for link in links]

    def update_link(self, link_id: str, user_id: str, title: Optional[str] = None, 
                   description: Optional[str] = None, category: Optional[str] = None,
                   tags: Optional[List[str]] = None, rating: Optional[int] = None) -> Dict:
        """
        Actualiza un enlace existente
        
        Args:
            link_id: ID del enlace
            user_id: ID del usuario
            title: Nuevo título (opcional)
            description: Nueva descripción (opcional)
            category: Nueva categoría (opcional)
            tags: Nuevas etiquetas (opcional)
            rating: Nueva calificación (opcional)
            
        Returns:
            Diccionario con los datos actualizados
            
        Raises:
            ValueError: Si el enlace no existe o no pertenece al usuario
        """
        # Preparar actualización
        update = {'updated_at': datetime.utcnow()}
        if title is not None:
            update['title'] = title
        if description is not None:
            update['description'] = description
        if category is not None:
            update['category'] = category
        if tags is not None:
            update['tags'] = tags
        if rating is not None:
            update['rating'] = rating
            
        result = self.links.update_one(
            {'_id': ObjectId(link_id), 'user_id': user_id},
            {'$set': update}
        )
        
        if result.modified_count == 0:
            raise ValueError('Enlace no encontrado o no pertenece al usuario')
            
        updated_link = self.links.find_one({'_id': ObjectId(link_id)})
        return {**updated_link, '_id': str(updated_link['_id'])}

    def delete_link(self, link_id: str, user_id: str) -> bool:
        """
        Elimina un enlace
        
        Args:
            link_id: ID del enlace
            user_id: ID del usuario
            
        Returns:
            True si el enlace fue eliminado, False si no
        """
        result = self.links.delete_one({'_id': ObjectId(link_id), 'user_id': user_id})
        return result.deleted_count > 0

    def increment_visits(self, link_id: str, user_id: str) -> bool:
        """
        Incrementa el contador de visitas de un enlace
        
        Args:
            link_id: ID del enlace
            user_id: ID del usuario
            
        Returns:
            True si se incrementó el contador, False si no
        """
        result = self.links.update_one(
            {'_id': ObjectId(link_id), 'user_id': user_id},
            {'$inc': {'visits': 1}, '$set': {'updated_at': datetime.utcnow()}}
        )
        return result.modified_count > 0

    def get_categories(self, user_id: str) -> List[Dict]:
        """
        Obtiene todas las categorías de un usuario
        
        Args:
            user_id: ID del usuario
            
        Returns:
            Lista de categorías
        """
        categories = self.categories.find({'user_id': user_id})
        return [{**cat, '_id': str(cat['_id'])} for cat in categories]

    def search_links(self, query: str, user_id: str) -> List[Dict]:
        """
        Busca enlaces por título, descripción o tags
        
        Args:
            query: Término de búsqueda
            user_id: ID del usuario
            
        Returns:
            Lista de enlaces que coinciden con la búsqueda
        """
        links = self.links.find({
            'user_id': user_id,
            '$or': [
                {'title': {'$regex': query, '$options': 'i'}},
                {'description': {'$regex': query, '$options': 'i'}},
                {'tags': {'$regex': query, '$options': 'i'}}
            ]
        })
        
        return [{**link, '_id': str(link['_id'])} for link in links]

    def get_link_by_id(self, link_id: str, user_id: str) -> Optional[Dict]:
        """
        Obtiene un enlace por su ID
        
        Args:
            link_id: ID del enlace
            user_id: ID del usuario
            
        Returns:
            Enlace si existe y pertenece al usuario, None si no
        """
        link = self.links.find_one({'_id': ObjectId(link_id), 'user_id': user_id})
        if link:
            return {**link, '_id': str(link['_id'])}
        return None

    def get_popular_links(self, user_id: str, limit: int = 10) -> List[Dict]:
        """
        Obtiene los enlaces más populares (basados en visitas y calificación)
        
        Args:
            user_id: ID del usuario
            limit: Número máximo de enlaces a devolver
            
        Returns:
            Lista de enlaces más populares
        """
        links = self.links.find(
            {'user_id': user_id}
        ).sort([
            ('visits', -1),
            ('rating', -1)
        ]).limit(limit)
        
        return [{**link, '_id': str(link['_id'])} for link in links]
