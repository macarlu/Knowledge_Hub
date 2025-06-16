from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, current_app
from datetime import datetime
import pytz
from . import mongo
import os
from werkzeug.utils import secure_filename
from .utils import descargar_web
import re
from bson import ObjectId
from flask import send_from_directory

main = Blueprint('main', __name__)

# Configurar la zona horaria
LOCAL_TZ = pytz.timezone('Europe/Madrid')

@main.route('/')
def index():
    
    # Obtener estadísticas de tipos de recursos
    estadisticas = {
        'enlaces': mongo.db.recursos.count_documents({'tipo': 'enlace'}),
        'notas': mongo.db.recursos.count_documents({'tipo': 'nota'}),
        'documentos': mongo.db.recursos.count_documents({'tipo': 'documento'})
    }
    eventos = list(mongo.db.eventos.find())
    calendar_events = []
    for evento in eventos:
        if "start" in evento and evento["start"]:
            calendar_events.append({
                "id": evento.get("id"),
                "title": evento.get("titulo", "Sin título"),
                "start": evento["start"].isoformat() if hasattr(evento["start"], 'isoformat') else str(evento["start"]),
                "description": evento.get("descripcion", ""),
                "color": evento.get("color", "#ffd43b")
        })
    else:
        print(f"⚠️ Evento sin 'start': {evento}")

    # Obtener recursos recientes
    notes = list(mongo.db.recursos.find({'tipo': 'nota'}).sort('fecha_creacion', -1).limit(5))
    documents = list(mongo.db.recursos.find({'tipo': 'documento'}).sort('fecha_creacion', -1).limit(5))
    links = list(mongo.db.recursos.find({'tipo': 'enlace'}).sort('fecha_creacion', -1).limit(5))
    
    recursos = list(mongo.db.recursos.find().sort('fecha_creacion', -1))  # Añade esta línea

    return render_template(
        'dashboard.html',
        calendar_events=calendar_events,
        estadisticas=estadisticas,
        notes=notes,
        documents=documents,
        links=links,
        recursos=recursos  # ← Añade esta variable
    )
@main.route('/add', methods=['GET'])
def add_resource_form():
    return render_template('add_resource.html')

@main.route('/add', methods=['POST'])
def add_resource():
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
            data['contenido'] = descargar_web(data['url'])
    
    elif tipo == 'nota':
        data['contenido'] = request.form.get('contenido', '')
    
    elif tipo == 'documento':
        if 'archivo' in request.files:
            archivo = request.files['archivo']
            if archivo.filename != '':
                filename = secure_filename(archivo.filename)
                filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
                archivo.save(filepath)
                data['ruta_archivo'] = filename
    
    mongo.db.recursos.insert_one(data)
    flash('Recurso añadido correctamente!', 'success')
    return redirect(url_for('main.index'))

@main.route('/search', methods=['GET'])
def search():
    query = request.args.get('q', '').strip()
    if not query:
        return redirect(url_for('main.index'))
    
    # Crear expresión regular para búsqueda
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
    
    # Paginación
    page = request.args.get('page', 1, type=int)
    per_page = 10
    skip = (page - 1) * per_page
    
    recursos = list(mongo.db.recursos.find(filtro).skip(skip).limit(per_page))
    total = mongo.db.recursos.count_documents(filtro)
    
    return render_template(
        'search.html',
        recursos=recursos,
        query=query,
        page=page,
        per_page=per_page,
        total=total
    )

@main.route('/edit/<resource_id>', methods=['GET'])
def edit_resource_form(resource_id):
    recurso = mongo.db.recursos.find_one_or_404({'_id': ObjectId(resource_id)})
    return render_template('edit_resource.html', recurso=recurso)

@main.route('/edit/<resource_id>', methods=['POST'])
def edit_resource(resource_id):
    updates = {
        "titulo": request.form['titulo'],
        "descripcion": request.form.get('descripcion', ''),
        "etiquetas": [tag.strip() for tag in request.form.get('etiquetas', '').split(',') if tag.strip()],
        "fecha_actualizacion": datetime.utcnow()
    }
    
    # Actualizar campos específicos
    tipo = request.form['tipo']
    if tipo == 'enlace':
        updates['url'] = request.form['url']
        if 'descargar' in request.form:
            updates['contenido'] = descargar_web(request.form['url'])
    elif tipo == 'nota':
        updates['contenido'] = request.form.get('contenido', '')
    
    mongo.db.recursos.update_one(
        {'_id': ObjectId(resource_id)},
        {'$set': updates}
    )
    
    flash('Recurso actualizado correctamente!', 'success')
    return redirect(url_for('main.index'))

@main.route('/delete/<resource_id>', methods=['POST'])
def delete_resource(resource_id):
    recurso = mongo.db.recursos.find_one({'_id': ObjectId(resource_id)})
    
    # Eliminar archivo físico si es documento
    if recurso['tipo'] == 'documento' and 'ruta_archivo' in recurso:
        try:
            file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], recurso['ruta_archivo'])
            if os.path.exists(file_path):
                os.remove(file_path)
        except Exception as e:
            flash(f'Error al eliminar el archivo: {str(e)}', 'warning')
    
    mongo.db.recursos.delete_one({'_id': ObjectId(resource_id)})
    flash('Recurso eliminado correctamente!', 'success')
    return redirect(url_for('main.index'))

@main.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(current_app.config['UPLOAD_FOLDER'], filename)

# ===== CALENDARIO =====
@main.route('/add_evento', methods=['POST'])
def add_evento():
    data = request.json
    
    evento = {
        "titulo": data['titulo'],
        "fecha_inicio": datetime.fromisoformat(data['fecha_inicio']),
        "descripcion": data.get('descripcion', ''),
        "color": data.get('color', '#3788d8')
    }
    
    if data.get('fecha_fin'):
        evento["fecha_fin"] = datetime.fromisoformat(data['fecha_fin'])
    
    # Insertar en MongoDB
    result = mongo.db.eventos.insert_one(evento)
    
    return jsonify({
        "success": True,
        "id": str(result.inserted_id)
    })

@main.route('/eventos')
def get_eventos():
    eventos = list(mongo.db.eventos.find({}))
    
    # Convertir ObjectId y fechas a formato serializable
    eventos_json = []
    for evento in eventos:
        evento['_id'] = str(evento['_id'])
        evento['fecha_inicio'] = evento['fecha_inicio'].isoformat()
        evento['fecha_fin'] = evento['fecha_fin'].isoformat() if 'fecha_fin' in evento else None
        eventos_json.append(evento)
    
    return jsonify(eventos_json)

@main.route('/calendario')
def calendario():
    return render_template('calendario.html')

@main.route('/documento/<doc_id>')
def ver_documento(doc_id):
    doc = mongo.db.documentos.find_one({"_id": ObjectId(doc_id)})
    if not doc:
        return "Documento no encontrado", 404

    ruta = doc.get("ruta_archivo")
    if not ruta:
        return "Ruta de archivo no válida", 400

    # Asumimos que está guardado en /uploads/
    return render_template("ver_documento.html", documento=doc, ruta_archivo=ruta)
