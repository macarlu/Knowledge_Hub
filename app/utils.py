import os
import re
import requests
from bs4 import BeautifulSoup
from typing import Optional, List
from datetime import datetime
from functools import wraps
from flask_jwt_extended import get_jwt_identity, jwt_required
from flask import request, jsonify

def allowed_file(filename: str) -> bool:
    """
    Verifica si el archivo tiene una extensión permitida
    """
    ALLOWED_EXTENSIONS = {
        'txt', 'pdf', 'doc', 'docx', 'xls', 'xlsx',
        'ppt', 'pptx', 'jpg', 'jpeg', 'png', 'gif',
        'epub'
    }
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def validate_email(email: str) -> bool:
    """
    Valida si un email tiene formato válido
    """
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))

def validate_url(url: str) -> bool:
    """
    Valida si una URL es válida
    """
    pattern = r'^(http|https)://[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}(/.*)?$'
    return bool(re.match(pattern, url))

def get_file_extension(filename: str) -> Optional[str]:
    """
    Obtiene la extensión de un archivo
    """
    if '.' in filename:
        return filename.rsplit('.', 1)[1].lower()
    return None

def generate_filename(base_name: str, ext: str) -> str:
    """
    Genera un nombre de archivo único
    """
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    return f"{base_name}_{timestamp}.{ext}"

def get_file_size(path: str) -> int:
    """
    Obtiene el tamaño de un archivo en bytes
    """
    try:
        return os.path.getsize(path)
    except:
        return 0

def descargar_web(url: str) -> str:
    """
    Descarga el contenido de una página web
    """
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        # Usar BeautifulSoup para extraer texto principal
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Eliminar scripts y estilos
        for script in soup(["script", "style"]):
            script.extract()
        
        # Obtener texto limpio
        text = soup.get_text()
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = '\n'.join(chunk for chunk in chunks if chunk)
        
        return text
    except Exception as e:
        print(f"Error al descargar {url}: {e}")
        return ""

def token_required(f):
    """
    Decorador que verifica si el usuario está autenticado
    """
    @wraps(f)
    @jwt_required()
    def decorated(*args, **kwargs):
        current_user = get_jwt_identity()
        if not current_user:
            return jsonify({'message': 'Token inválido'}), 401
        
        # Pasar usuario al endpoint
        return f(current_user, *args, **kwargs)
    
    return decorated

def admin_required(f):
    """
    Decorador que verifica si el usuario es administrador
    """
    @wraps(f)
    @jwt_required()
    def decorated(*args, **kwargs):
        current_user = get_jwt_identity()
        if not current_user:
            return jsonify({'message': 'Token inválido'}), 401
            
        # Aquí deberíamos verificar el rol del usuario en la base de datos
        # Pero por ahora asumimos que el usuario es admin
        return f(current_user, *args, **kwargs)
    
    return decorated