from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from bson.objectid import ObjectId
from pymongo.errors import DuplicateKeyError
from ..models.calendar import Event, Reminder
from enum import Enum

class EventCategory(Enum):
    """
    Enum para categorías de eventos
    """
    MEETING = "meeting"
    TASK = "task"
    PERSONAL = "personal"
    WORK = "work"
    OTHER = "other"

class CalendarService:
    """
    Servicio que maneja toda la lógica relacionada con el calendario
    """
    
    def __init__(self, db):
        """
        Inicializa el servicio con la conexión a la base de datos
        Args:
            db: Conexión a MongoDB
        """
        self.db = db
        self.collection = self.db['events']
        
        # Crear índices únicos para evitar duplicados
        self.collection.create_index([('title', 1), ('start_time', 1), ('user_id', 1)], unique=True)

    def create_event(self, title: str, description: str, start_time: datetime, 
                    end_time: datetime, all_day: bool, user_id: str, 
                    location: Optional[str] = None, category: Optional[str] = None,
                    reminders: Optional[List[Dict]] = None) -> Dict:
        """
        Crea un nuevo evento en el calendario
        
        Args:
            title: Título del evento
            description: Descripción del evento
            start_time: Fecha y hora de inicio
            end_time: Fecha y hora de fin
            all_day: Indica si es un evento de todo el día
            user_id: ID del usuario que crea el evento
            location: Lugar del evento (opcional)
            category: Categoría del evento (opcional)
            reminders: Lista de recordatorios (opcional)
            
        Returns:
            Diccionario con los datos del evento creado
            
        Raises:
            ValueError: Si ya existe un evento con el mismo título y hora
        """
        try:
            # Validar que la fecha de fin sea posterior a la de inicio
            if end_time <= start_time:
                raise ValueError('La fecha de fin debe ser posterior a la fecha de inicio')
                
            event = {
                'title': title,
                'description': description,
                'start_time': start_time,
                'end_time': end_time,
                'all_day': all_day,
                'location': location,
                'category': category,
                'reminders': reminders or [],
                'user_id': user_id,
                'created_at': datetime.utcnow(),
                'updated_at': datetime.utcnow()
            }
            
            # Intentar insertar el evento
            result = self.collection.insert_one(event)
            event['_id'] = str(result.inserted_id)
            return event
            
        except DuplicateKeyError:
            raise ValueError('Ya existe un evento con el mismo título y hora')

    def get_events(self, user_id: str, start_date: Optional[datetime] = None, 
                  end_date: Optional[datetime] = None, category: Optional[str] = None) -> List[Dict]:
        """
        Obtiene los eventos de un usuario dentro de un rango de fechas
        
        Args:
            user_id: ID del usuario
            start_date: Fecha de inicio del rango (opcional)
            end_date: Fecha de fin del rango (opcional)
            category: Categoría del evento (opcional)
            
        Returns:
            Lista de eventos que cumplen con los criterios
        """
        query = {'user_id': user_id}
        
        # Agregar filtros opcionales
        if start_date:
            query['start_time'] = {'$gte': start_date}
        if end_date:
            query['end_time'] = {'$lte': end_date}
        if category:
            query['category'] = category
            
        events = self.collection.find(query)
        return [{**event, '_id': str(event['_id'])} for event in events]

    def update_event(self, event_id: str, user_id: str, title: str, description: str, 
                    start_time: datetime, end_time: datetime, all_day: bool,
                    location: Optional[str] = None, category: Optional[str] = None,
                    reminders: Optional[List[Dict]] = None) -> Dict:
        """
        Actualiza un evento existente
        
        Args:
            event_id: ID del evento a actualizar
            user_id: ID del usuario
            title: Nuevo título
            description: Nueva descripción
            start_time: Nueva fecha de inicio
            end_time: Nueva fecha de fin
            all_day: Indicador de todo el día
            location: Nueva ubicación
            category: Nueva categoría
            reminders: Nuevos recordatorios
            
        Returns:
            Diccionario con los datos actualizados
            
        Raises:
            ValueError: Si el evento no existe o no pertenece al usuario
        """
        # Validar que la fecha de fin sea posterior a la de inicio
        if end_time <= start_time:
            raise ValueError('La fecha de fin debe ser posterior a la fecha de inicio')
            
        result = self.collection.update_one(
            {'_id': ObjectId(event_id), 'user_id': user_id},
            {
                '$set': {
                    'title': title,
                    'description': description,
                    'start_time': start_time,
                    'end_time': end_time,
                    'all_day': all_day,
                    'location': location,
                    'category': category,
                    'reminders': reminders,
                    'updated_at': datetime.utcnow()
                }
            }
        )
        
        if result.modified_count == 0:
            raise ValueError('Evento no encontrado o no pertenece al usuario')
            
        updated_event = self.collection.find_one({'_id': ObjectId(event_id)})
        return {**updated_event, '_id': str(updated_event['_id'])}

    def delete_event(self, event_id: str, user_id: str) -> bool:
        """
        Elimina un evento
        
        Args:
            event_id: ID del evento
            user_id: ID del usuario
            
        Returns:
            True si el evento fue eliminado, False si no
        """
        result = self.collection.delete_one({'_id': ObjectId(event_id), 'user_id': user_id})
        return result.deleted_count > 0

    def get_upcoming_events(self, user_id: str, days: int = 7) -> List[Dict]:
        """
        Obtiene los eventos próximos de un usuario
        
        Args:
            user_id: ID del usuario
            days: Número de días a considerar
            
        Returns:
            Lista de eventos próximos
        """
        now = datetime.utcnow()
        end_date = now + timedelta(days=days)
        
        return self.get_events(
            user_id=user_id,
            start_date=now,
            end_date=end_date
        )

    def get_events_by_category(self, user_id: str, category: str) -> List[Dict]:
        """
        Obtiene los eventos de un usuario por categoría
        
        Args:
            user_id: ID del usuario
            category: Categoría del evento
            
        Returns:
            Lista de eventos de la categoría especificada
        """
        return self.get_events(user_id=user_id, category=category)

    def create_reminder(self, event_id: str, user_id: str, 
                       time_before: int, notification_type: str) -> Dict:
        """
        Crea un recordatorio para un evento
        
        Args:
            event_id: ID del evento
            user_id: ID del usuario
            time_before: Tiempo antes del evento (en minutos)
            notification_type: Tipo de notificación
            
        Returns:
            Diccionario con los datos del recordatorio
            
        Raises:
            ValueError: Si el evento no existe o no pertenece al usuario
        """
        # Primero verificar si el evento existe y pertenece al usuario
        event = self.collection.find_one({'_id': ObjectId(event_id), 'user_id': user_id})
        if not event:
            raise ValueError('Evento no encontrado o no pertenece al usuario')
            
        reminder = {
            'id': str(ObjectId()),
            'time_before': time_before,
            'notification_type': notification_type,
            'sent': False
        }
        
        # Agregar el recordatorio al evento
        result = self.collection.update_one(
            {'_id': ObjectId(event_id), 'user_id': user_id},
            {'$push': {'reminders': reminder}}
        )
        
        if result.modified_count == 0:
            raise ValueError('No se pudo agregar el recordatorio')
            
        return reminder

    def get_reminders(self, user_id: str) -> List[Dict]:
        """
        Obtiene todos los recordatorios pendientes de un usuario
        
        Args:
            user_id: ID del usuario
            
        Returns:
            Lista de recordatorios pendientes
        """
        events = self.collection.find(
            {'user_id': user_id},
            {'reminders': 1, '_id': 0}
        )
        
        reminders = []
        for event in events:
            for reminder in event.get('reminders', []):
                if not reminder.get('sent', False):
                    reminders.append(reminder)
        
        return reminders

    def mark_reminder_as_sent(self, event_id: str, user_id: str, reminder_id: str) -> bool:
        """
        Marca un recordatorio como enviado
        
        Args:
            event_id: ID del evento
            user_id: ID del usuario
            reminder_id: ID del recordatorio
            
        Returns:
            True si el recordatorio fue marcado, False si no
        """
        result = self.collection.update_one(
            {
                '_id': ObjectId(event_id),
                'user_id': user_id,
                'reminders.id': reminder_id
            },
            {'$set': {'reminders.$.sent': True}}
        )
        
        return result.modified_count > 0
