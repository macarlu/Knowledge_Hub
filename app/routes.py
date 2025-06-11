from flask import Blueprint, render_template, request, redirect, url_for, flash
from datetime import datetime
from . import mongo
import os
from werkzeug.utils import secure_filename
from .utils import descargar_web  # Lo implementaremos después
from flask import current_app
import re
from bson import ObjectId
from flask import send_from_directory

main = Blueprint('main', __name__)

@main.route('/')
def index():
    # Obtener estadísticas de tipos de recursos
    estadisticas = {
        'enlaces': mongo.db.recursos.count_documents({'tipo': 'enlace'}),
        'notas': mongo.db.recursos.count_documents({'tipo': 'nota'}),
        'documentos': mongo.db.recursos.count_documents({'tipo': 'documento'})
    }
    # Notas rápidas (últimas 5)
    notes = list(mongo.db.recursos.find({'tipo': 'nota'}).sort('fecha_creacion', -1).limit(5))
    # Documentos importantes (últimos 5)
    documents = list(mongo.db.recursos.find({'tipo': 'documento'}).sort('fecha_creacion', -1).limit(5))
    # Enlaces recientes (últimos 5)
    links = list(mongo.db.recursos.find({'tipo': 'enlace'}).sort('fecha_creacion', -1).limit(5))
    # Leer eventos de la colección 'eventos'
    eventos = list(mongo.db.eventos.find())
    calendar_events = [
        {
            "title": event["title"],
            "start": event["date"].isoformat() if hasattr(event["date"], 'isoformat') else str(event["date"])
        } for event in eventos
    ]
    # Ejemplo: cada nota se muestra como evento en el calendario
    calendar_events += [
        {
            "title": note.get("titulo", note.get("title", "Nota")),
            "start": note["fecha_creacion"].isoformat() if hasattr(note["fecha_creacion"], 'isoformat') else str(note["fecha_creacion"])
        }
        for note in notes
    ]
    return render_template(
        'dashboard.html',
        estadisticas=estadisticas,
        notes=notes,
        documents=documents,
        links=links,
        calendar_events=calendar_events
    )

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
        "fecha_actualizacion": None,
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
    # Paginación de resultados
    page = request.args.get('page', 1, type=int)
    per_page = 10
    skip = (page - 1) * per_page
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
    recursos = list(mongo.db.recursos.find(filtro).skip(skip).limit(per_page))
    total = mongo.db.recursos.count_documents(filtro)
    return render_template(
        'search_results.html',
        recursos=recursos,
        query=query,
        tipos=tipos,
        etiquetas_populares=etiquetas_populares,
        page=page,
        per_page=per_page,
        total=total
    )

@main.route('/edit/<resource_id>', methods=['GET', 'POST'])
def edit_resource(resource_id):
    from bson.objectid import ObjectId
    recurso = mongo.db.recursos.find_one({'_id': ObjectId(resource_id)})
    if not recurso:
        flash('Recurso no encontrado.', 'danger')
        return redirect(url_for('main.index'))
    if request.method == 'POST':
        # Actualizar los campos editables
        update_data = {
            'titulo': request.form['titulo'],
            'descripcion': request.form.get('descripcion', ''),
            'etiquetas': [tag.strip() for tag in request.form.get('etiquetas', '').split(',') if tag.strip()]
        }
        update_data["fecha_actualizacion"] = datetime.utcnow()
        # Guardar historial de cambios
        historial = {
            'fecha': datetime.utcnow(),
            'usuario': 'current_user',  # Cambia esto cuando tengas autenticación
            'cambios': update_data.copy()
        }
        mongo.db.recursos.update_one({'_id': ObjectId(resource_id)}, {'$set': update_data})
        mongo.db.recursos.update_one({'_id': ObjectId(resource_id)}, {'$push': {'historial': historial}})
        flash('Recurso actualizado correctamente.', 'success')
        return redirect(url_for('main.index'))
    return render_template('add_resource.html', recurso=recurso, edit_mode=True)

@main.route('/delete/<resource_id>', methods=['POST'])
def delete_resource(resource_id):
    from bson.objectid import ObjectId
    mongo.db.recursos.delete_one({'_id': ObjectId(resource_id)})
    flash('Recurso eliminado correctamente.', 'success')
    return redirect(url_for('main.index'))

@main.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(current_app.config['UPLOAD_FOLDER'], filename)

@main.route('/add_event', methods=['POST'])
def add_event():
    title = request.form.get('title')
    date = request.form.get('date')
    print(f"DEBUG EVENT: title={title}, date={date}")  # <-- Esto imprime en consola
    # Convertir a formato ISO completo (YYYY-MM-DDT00:00:00)
    if date and len(date) == 10:
        date = date + 'T00:00:00'
    try:
        date_obj = datetime.fromisoformat(date) if date else datetime.utcnow()
    except Exception as e:
        print(f"ERROR PARSING DATE: {e}")
        date_obj = datetime.utcnow()
    result = mongo.db.eventos.insert_one({
        'title': title,
        'date': date_obj
    })
    print(f"DEBUG EVENT INSERTED: {result.inserted_id}")
    flash('Evento añadido correctamente.', 'success')
    return redirect(url_for('main.index'))