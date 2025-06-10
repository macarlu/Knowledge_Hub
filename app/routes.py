from flask import Blueprint, render_template, request, redirect, url_for, flash
from datetime import datetime
from . import mongo
import os
from werkzeug.utils import secure_filename
from .utils import descargar_web  # Lo implementaremos después

main = Blueprint('main', __name__)

@main.route('/')
def index():
    recursos = list(mongo.db.recursos.find().limit(10))
    return render_template('index.html', recursos=recursos)

@main.route('/add', methods=['GET'])
def add_resource_form():
    return render_template('add_resource.html')

@main.route('/add', methods=['POST'])
def add_resource():
    # Recoger datos del formulario
    data = {
        "tipo": request.form['tipo'],
        "titulo": request.form['titulo'],
        "descripcion": request.form.get('descripcion', ''),
        "etiquetas": [tag.strip() for tag in request.form.get('etiquetas', '').split(',') if tag.strip()],
        "fecha_creacion": datetime.utcnow(),
        "favorito": False,
        "para_revisar": False
    }
    
    # Procesar según el tipo de recurso
    tipo = data['tipo']
    
    if tipo == 'enlace':
        data['url'] = request.form['url']
        if 'descargar' in request.form:
            data['contenido'] = descargar_web(data['url'])  # Función que implementaremos
    
    elif tipo == 'nota':
        data['contenido'] = request.form.get('contenido', '')
    
    elif tipo == 'documento':
        if 'archivo' in request.files:
            archivo = request.files['archivo']
            if archivo.filename != '':
                # Guardar el archivo
                filename = secure_filename(archivo.filename)
                filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
                archivo.save(filepath)
                data['ruta_archivo'] = filename
    
    # Insertar en MongoDB
    mongo.db.recursos.insert_one(data)
    
    flash('Recurso añadido correctamente!', 'success')
    return redirect(url_for('main.index'))