from flask import Flask
from flask_pymongo import PyMongo
import os

mongo = PyMongo()

def create_app():
    app = Flask(__name__)
    app.config["MONGO_URI"] = "mongodb://localhost:27017/knowledgehub"
    app.config['UPLOAD_FOLDER'] = '/app/uploads'  # Ruta dentro del contenedor
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB
    app.secret_key = 'supersecretkey'  # Para mensajes flash
    
    # Crear directorio de uploads si no existe
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])
    
    mongo.init_app(app)
    
    from .routes import main
    app.register_blueprint(main)
    
    return app