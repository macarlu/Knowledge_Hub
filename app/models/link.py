from datetime import datetime
from typing import Optional, List
from dataclasses import dataclass
from enum import Enum

@dataclass
class Link:
    """
    Clase que representa un enlace
    
    Atributos:
        id: ID único del enlace
        url: URL del enlace
        title: Título del enlace
        description: Descripción del enlace
        category: Categoría del enlace
        tags: Lista de etiquetas
        rating: Calificación del enlace
        visits: Número de visitas
        user_id: ID del usuario que añadió el enlace
        created_at: Fecha de creación
        updated_at: datetime
    """
    
    id: str
    url: str
    title: str
    description: str
    category: str
    tags: List[str]
    rating: int
    visits: int
    user_id: str
    created_at: datetime
    updated_at: datetime

@dataclass
class LinkCategory:
    """
    Clase que representa una categoría de enlaces
    
    Atributos:
        id: ID único de la categoría
        name: Nombre de la categoría
        description: Descripción de la categoría
        user_id: ID del usuario
        created_at: Fecha de creación
    """
    
    id: str
    name: str
    description: str
    user_id: str
    created_at: datetime
