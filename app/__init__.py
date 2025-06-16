from flask import Flask
from flask_pymongo import PyMongo
from flask_jwt_extended import JWTManager
from flask_login import LoginManager, current_user
from bson import ObjectId
from .config import config
from .models.user import User
import os
from dotenv import load_dotenv

mongo = PyMongo()
jwt = JWTManager()
login_manager = LoginManager()

load_dotenv()

def create_app(config_name='default'):
    """
    Crea y configura la aplicación Flask
    Args:
        config_name: Nombre de la configuración ('development', 'production')
    Returns:
        La aplicación Flask configurada
    """
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    
    # Crear directorio de uploads si no existe
    upload_folder = app.config['UPLOAD_FOLDER']
    if not os.path.exists(upload_folder):
        os.makedirs(upload_folder)
    
    # Inicializar extensiones
    mongo.init_app(app)
    jwt.init_app(app)
    login_manager.init_app(app)
    
    # Configurar LoginManager
    login_manager.login_view = 'main.login'
    login_manager.login_message = 'Por favor, inicia sesión para acceder a esta página.'
    login_manager.login_message_category = 'info'
    
    @login_manager.user_loader
    def load_user(user_id):
        user = mongo.db.users.find_one({'_id': ObjectId(user_id)})
        if user:
            return User(
                id=str(user['_id']),
                email=user['email'],
                password_hash=user['password_hash'],
                name=user['name'],
                role=user['role'],
                created_at=user['created_at'],
                last_login=user['last_login'],
                active=user['active'],
                avatar=user.get('avatar')
            )
        return None
    
    # Inicializar servicios
    from .services import CalendarService, NotesService, DocumentsService, LinksService, AuthService
    app.calendar_service = CalendarService(mongo.db)
    app.notes_service = NotesService(mongo.db)
    app.documents_service = DocumentsService(mongo.db, upload_folder)
    app.links_service = LinksService(mongo.db)
    app.auth_service = AuthService(mongo.db, app.config['SECRET_KEY'])
    
    # Registrar blueprints
    from .routes import api_bp, main, calendar, documents, links, epub
    app.register_blueprint(main)
    app.register_blueprint(api_bp)
    app.register_blueprint(calendar)
    app.register_blueprint(documents)
    app.register_blueprint(links)
    app.register_blueprint(epub.epub_bp, url_prefix='/epub')
    
    # Configurar JWT
    @jwt.user_identity_loader
    def user_identity_lookup(user):
        return user['_id']
    
    @jwt.user_lookup_loader
    def user_lookup_callback(_jwt_header, jwt_data):
        identity = jwt_data["sub"]
        return app.auth_service.get_user_by_id(identity)
    
    return app