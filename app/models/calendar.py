from datetime import datetime
from typing import List, Optional
from dataclasses import dataclass
from enum import Enum

@dataclass
class Event:
    """
    Clase que representa un evento del calendario
    
    Atributos:
        id: ID único del evento
        title: Título del evento
        description: Descripción del evento
        start_time: Fecha y hora de inicio
        end_time: Fecha y hora de fin
        all_day: Indica si es un evento de todo el día
        user_id: ID del usuario que creó el evento
        created_at: Fecha de creación
        updated_at: Fecha de última actualización
        location: Lugar del evento
        category: Categoría del evento
        reminders: Lista de recordatorios
    """
    
    id: str
    title: str
    description: str
    start_time: datetime
    end_time: datetime
    all_day: bool
    user_id: str
    created_at: datetime
    updated_at: datetime
    location: Optional[str] = None
    category: Optional[str] = None
    reminders: List['Reminder'] = None

@dataclass
class Reminder:
    """
    Clase que representa un recordatorio para un evento
    
    Atributos:
        id: ID único del recordatorio
        time_before: Tiempo antes del evento (en minutos)
        notification_type: Tipo de notificación
        sent: Indica si el recordatorio ha sido enviado
    """
    
    id: str
    time_before: int
    notification_type: str
    sent: bool = False
