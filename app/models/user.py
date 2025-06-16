from datetime import datetime
from typing import Optional
from dataclasses import dataclass
from enum import Enum
from flask_login import UserMixin

@dataclass
class User(UserMixin):
    """
    Clase que representa un usuario
    
    Atributos:
        id: ID único del usuario
        email: Email del usuario
        password_hash: Hash de la contraseña
        name: Nombre completo
        role: Rol del usuario
        created_at: Fecha de creación
        last_login: Fecha del último login
        active: Indica si el usuario está activo
        avatar: URL del avatar
    """
    
    id: str
    email: str
    password_hash: str
    name: str
    role: str
    created_at: datetime
    last_login: datetime
    active: bool
    avatar: Optional[str] = None

    def get_id(self):
        return self.id

    @property
    def is_active(self):
        return self.active

    @property
    def is_authenticated(self):
        return True

    @property
    def is_anonymous(self):
        return False

@dataclass
class UserRole(Enum):
    """
    Enum para roles de usuario
    """
    ADMIN = "admin"
    USER = "user"
    GUEST = "guest"
