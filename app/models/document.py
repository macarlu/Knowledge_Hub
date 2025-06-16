from datetime import datetime
from typing import Optional, List
from dataclasses import dataclass
from enum import Enum

@dataclass
class Document:
    """
    Clase que representa un documento
    
    Atributos:
        id: ID único del documento
        title: Título del documento
        description: Descripción del documento
        file_name: Nombre del archivo
        file_path: Ruta del archivo
        file_type: Tipo de archivo
        size: Tamaño del archivo en bytes
        tags: Lista de etiquetas
        categories: Lista de categorías
        version: Número de versión
        user_id: ID del usuario que subió el documento
        created_at: Fecha de creación
        updated_at: Fecha de última actualización
    """
    
    id: str
    title: str
    description: str
    file_name: str
    file_path: str
    file_type: str
    size: int
    tags: List[str]
    categories: List[str]
    version: int
    user_id: str
    created_at: datetime
    updated_at: datetime

@dataclass
class DocumentVersion:
    """
    Clase que representa una versión de un documento
    
    Atributos:
        id: ID único de la versión
        document_id: ID del documento
        file_path: Ruta del archivo
        version_number: Número de versión
        changes: Descripción de los cambios
        user_id: ID del usuario que hizo los cambios
        created_at: Fecha de creación
    """
    
    id: str
    document_id: str
    file_path: str
    version_number: int
    changes: str
    user_id: str
    created_at: datetime
