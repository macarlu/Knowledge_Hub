import os
from typing import Optional, List

def allowed_file(filename: str) -> bool:
    """
    Verifica si el archivo tiene una extensión permitida
    """
    ALLOWED_EXTENSIONS = {
        'txt', 'pdf', 'doc', 'docx', 'xls', 'xlsx',
        'ppt', 'pptx', 'jpg', 'jpeg', 'png', 'gif'
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
