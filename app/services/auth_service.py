from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from bson.objectid import ObjectId
import jwt
from werkzeug.security import generate_password_hash, check_password_hash
from ..models.user import User, UserRole
from .utils import validate_email

class AuthService:
    """
    Servicio que maneja la autenticación de usuarios
    """
    
    def __init__(self, db, secret_key: str, token_expiration: int = 3600):
        """
        Inicializa el servicio de autenticación
        Args:
            db: Conexión a MongoDB
            secret_key: Clave secreta para JWT
            token_expiration: Tiempo de expiración del token en segundos
        """
        self.db = db
        self.users = self.db['users']
        self.secret_key = secret_key
        self.token_expiration = token_expiration
        
        # Crear índice único para email
        self.users.create_index('email', unique=True)

    def register_user(self, email: str, password: str, name: str) -> Dict:
        """
        Registra un nuevo usuario
        
        Args:
            email: Email del usuario
            password: Contraseña del usuario
            name: Nombre completo del usuario
            
        Returns:
            Diccionario con los datos del usuario registrado
            
        Raises:
            ValueError: Si el email ya está registrado
        """
        # Validar email
        if not validate_email(email):
            raise ValueError('Email no válido')
            
        # Verificar si el email ya existe
        if self.users.find_one({'email': email}):
            raise ValueError('Email ya registrado')
            
        # Hash de la contraseña
        password_hash = generate_password_hash(password)
        
        # Crear usuario
        user = {
            'email': email,
            'password_hash': password_hash,
            'name': name,
            'role': UserRole.USER.value,
            'created_at': datetime.utcnow(),
            'last_login': None,
            'active': True,
            'avatar': None
        }
        
        result = self.users.insert_one(user)
        user['_id'] = str(result.inserted_id)
        
        # Eliminar el hash de la contraseña antes de devolver
        del user['password_hash']
        return user

    def login_user(self, email: str, password: str) -> Dict:
        """
        Inicia sesión de un usuario
        
        Args:
            email: Email del usuario
            password: Contraseña del usuario
            
        Returns:
            Diccionario con los datos del usuario y el token JWT
            
        Raises:
            ValueError: Si las credenciales son inválidas
        """
        # Buscar usuario
        user = self.users.find_one({'email': email})
        if not user or not check_password_hash(user['password_hash'], password):
            raise ValueError('Credenciales inválidas')
            
        # Actualizar último login
        self.users.update_one(
            {'email': email},
            {'$set': {'last_login': datetime.utcnow()}}
        )
        
        # Generar token JWT
        token = self._generate_token(user)
        
        # Preparar respuesta
        user['_id'] = str(user['_id'])
        del user['password_hash']
        
        return {
            'user': user,
            'token': token
        }

    def verify_token(self, token: str) -> Optional[Dict]:
        """
        Verifica un token JWT
        
        Args:
            token: Token JWT a verificar
            
        Returns:
            Datos del usuario si el token es válido, None si no
        """
        try:
            # Decodificar token
            data = jwt.decode(token, self.secret_key, algorithms=['HS256'])
            user_id = data.get('user_id')
            
            # Buscar usuario
            user = self.users.find_one({'_id': ObjectId(user_id)})
            if user and user.get('active'):
                user['_id'] = str(user['_id'])
                del user['password_hash']
                return user
            
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None
            
        return None

    def _generate_token(self, user: Dict) -> str:
        """
        Genera un token JWT
        
        Args:
            user: Datos del usuario
            
        Returns:
            Token JWT
        """
        payload = {
            'user_id': str(user['_id']),
            'email': user['email'],
            'role': user['role'],
            'exp': datetime.utcnow() + timedelta(seconds=self.token_expiration)
        }
        return jwt.encode(payload, self.secret_key, algorithm='HS256')

    def get_user_by_id(self, user_id: str) -> Optional[Dict]:
        """
        Obtiene un usuario por su ID
        
        Args:
            user_id: ID del usuario
            
        Returns:
            Datos del usuario si existe y está activo, None si no
        """
        user = self.users.find_one({'_id': ObjectId(user_id)})
        if user and user.get('active'):
            user['_id'] = str(user['_id'])
            del user['password_hash']
            return user
        return None

    def update_user(self, user_id: str, data: Dict) -> Dict:
        """
        Actualiza los datos de un usuario
        
        Args:
            user_id: ID del usuario
            data: Datos a actualizar
            
        Returns:
            Datos del usuario actualizado
            
        Raises:
            ValueError: Si el usuario no existe o no está activo
        """
        # Validar email si se proporciona
        if 'email' in data and not validate_email(data['email']):
            raise ValueError('Email no válido')
            
        # Actualizar usuario
        result = self.users.update_one(
            {'_id': ObjectId(user_id)},
            {'$set': data}
        )
        
        if result.modified_count == 0:
            raise ValueError('Usuario no encontrado o no activo')
            
        # Obtener usuario actualizado
        user = self.users.find_one({'_id': ObjectId(user_id)})
        user['_id'] = str(user['_id'])
        del user['password_hash']
        return user
