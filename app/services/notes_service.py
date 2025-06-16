from datetime import datetime
from typing import List, Optional
from bson.objectid import ObjectId
from pymongo.errors import DuplicateKeyError

class NotesService:
    """
    Servicio que maneja toda la lógica relacionada con las notas
    """
    def __init__(self, db):
        self.db = db
        self.collection = self.db['notes']

    def create_note(self, title: str, content: str, tags: List[str], user_id: str) -> dict:
        """
        Crea una nueva nota
        Args:
            title: Título de la nota
            content: Contenido de la nota
            tags: Lista de etiquetas
            user_id: ID del usuario que crea la nota
        Returns:
            Diccionario con los datos de la nota creada
        """
        try:
            note = {
                'title': title,
                'content': content,
                'tags': tags,
                'user_id': user_id,
                'created_at': datetime.utcnow(),
                'updated_at': datetime.utcnow()
            }
            result = self.collection.insert_one(note)
            note['_id'] = str(result.inserted_id)
            return note
        except DuplicateKeyError:
            raise ValueError('Ya existe una nota con este título')

    def get_notes(self, user_id: str, tag: Optional[str] = None) -> List[dict]:
        """
        Obtiene todas las notas del usuario
        Args:
            user_id: ID del usuario
            tag: Etiqueta opcional para filtrar
        Returns:
            Lista de notas
        """
        query = {'user_id': user_id}
        if tag:
            query['tags'] = tag
        
        notes = self.collection.find(query)
        return [{**note, '_id': str(note['_id'])} for note in notes]

    def update_note(self, note_id: str, user_id: str, title: str, content: str, tags: List[str]) -> dict:
        """
        Actualiza una nota existente
        Args:
            note_id: ID de la nota
            user_id: ID del usuario
            title: Nuevo título
            content: Nuevo contenido
            tags: Nuevas etiquetas
        Returns:
            Diccionario con los datos actualizados
        """
        result = self.collection.update_one(
            {'_id': ObjectId(note_id), 'user_id': user_id},
            {
                '$set': {
                    'title': title,
                    'content': content,
                    'tags': tags,
                    'updated_at': datetime.utcnow()
                }
            }
        )
        
        if result.modified_count == 0:
            raise ValueError('Nota no encontrada o no pertenece al usuario')
            
        updated_note = self.collection.find_one({'_id': ObjectId(note_id)})
        return {**updated_note, '_id': str(updated_note['_id'])}

    def delete_note(self, note_id: str, user_id: str) -> bool:
        """
        Elimina una nota
        Args:
            note_id: ID de la nota
            user_id: ID del usuario
        Returns:
            True si la nota fue eliminada, False si no
        """
        result = self.collection.delete_one({'_id': ObjectId(note_id), 'user_id': user_id})
        return result.deleted_count > 0
