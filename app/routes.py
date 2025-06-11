from flask import Blueprint, render_template, request, redirect, url_for, flash
from datetime import datetime
from . import mongo
import os
from werkzeug.utils import secure_filename
from .utils import descargar_web  # Lo implementaremos después
from flask import current_app
import re

main = Blueprint('main', __name__)

@main.route('/')
def index():
    # Obtener estadísticas de tipos de recursos
    estadisticas = {
        'enlaces': mongo.db.recursos.count_documents({'tipo': 'enlace'}),
        'notas': mongo.db.recursos.count_documents({'tipo': 'nota'}),
        'documentos': mongo.db.recursos.count_documents({'tipo': 'documento'})
    }
    
    # Obtener últimos 10 recursos
    recursos = list(mongo.db.recursos.find().sort('fecha_creacion', -1).limit(10))
    
    return render_template('index.html', recursos=recursos, estadisticas=estadisticas)

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

@main.route('/search', methods=['GET'])
def search():
    query = request.args.get('q', '').strip()
    
    if not query:
        return redirect(url_for('main.index'))
    
    # En la ruta de búsqueda
tipos = mongo.db.recursos.distinct('tipo')
etiquetas_populares = mongo.db.recursos.aggregate([
    {'$unwind': '$etiquetas'},
    {'$group': {'_id': '$etiquetas', 'count': {'$sum': 1}}},
    {'$sort': {'count': -1}},
    {'$limit': 10}
])
    
    # Crear una expresión regular para búsqueda insensible a mayúsculas/minúsculas
    regex = re.compile(f'.*{re.escape(query)}.*', re.IGNORECASE)
    
    # Buscar en múltiples campos
    filtro = {
        '$or': [
            {'titulo': {'$regex': regex}},
            {'descripcion': {'$regex': regex}},
            {'contenido': {'$regex': regex}},
            {'etiquetas': {'$regex': regex}}
        ]
    }
    
    recursos = list(mongo.db.recursos.find(filtro))
    return render_template('search_results.html', recursos=recursos, query=query)