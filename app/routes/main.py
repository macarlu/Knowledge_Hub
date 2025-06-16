from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, current_app, session
from datetime import datetime, timedelta
import pytz
from .. import mongo
from werkzeug.security import check_password_hash, generate_password_hash
from flask_login import login_user, logout_user, current_user, login_required
from ..models.user import User
import os
from werkzeug.utils import secure_filename
from ..utils import descargar_web, validate_url, allowed_file
from bson import ObjectId
from flask import send_from_directory
from ..services.calendar_service import CalendarService

main = Blueprint('main', __name__)

# Configurar la zona horaria
LOCAL_TZ = pytz.timezone('Europe/Madrid')

@main.route('/')
@login_required
def index():
    # Obtener estadísticas de tipos de recursos
    stats = {
        'eventos': mongo.db.events.count_documents({}),
        'documentos': mongo.db.documents.count_documents({}),
        'enlaces': mongo.db.links.count_documents({}),
        'notas': mongo.db.notes.count_documents({})
    }
    
    # Obtener notas
    notes = mongo.db.notes.find().sort('fecha_creacion', -1).limit(5)
    
    # Obtener documentos
    documents = mongo.db.documents.find().sort('fecha_creacion', -1).limit(5)
    
    # Obtener enlaces
    links = mongo.db.links.find().sort('fecha_creacion', -1).limit(5)
    
    # Obtener recursos agrupados por etiquetas
    recursos = []
    
    # Obtener documentos
    for doc in mongo.db.documents.find():
        recurso = {
            'tipo': 'documento',
            'titulo': doc.get('nombre', 'Sin título'),
            'descripcion': doc.get('descripcion', ''),
            'fecha_creacion': doc.get('fecha_subida', datetime.now()),
            'tags': doc.get('tags', []),
            '_id': str(doc.get('_id')) if doc.get('_id') else '0',
            'ruta_archivo': doc.get('ruta_archivo', ''),
            'contenido': None
        }
        recursos.append(recurso)
    
    # Obtener enlaces
    for link in mongo.db.links.find():
        recurso = {
            'tipo': 'enlace',
            'titulo': link.get('titulo', 'Sin título'),
            'descripcion': link.get('descripcion', ''),
            'fecha_creacion': link.get('fecha_creacion', datetime.now()),
            'tags': link.get('tags', []),
            '_id': str(link.get('_id')) if link.get('_id') else '0',
            'url': link.get('url', ''),
            'contenido': None
        }
        recursos.append(recurso)
    
    # Obtener notas
    for note in mongo.db.notes.find():
        recurso = {
            'tipo': 'nota',
            'titulo': note.get('titulo', 'Sin título'),
            'descripcion': note.get('descripcion', ''),
            'fecha_creacion': note.get('fecha_creacion', datetime.now()),
            'tags': note.get('tags', []),
            '_id': str(note.get('_id')) if note.get('_id') else '0',
            'contenido': note.get('contenido', '')
        }
        recursos.append(recurso)
    
    # Ordenar recursos por fecha de creación
    recursos = sorted(recursos, key=lambda x: x.get('fecha_creacion', datetime.now()), reverse=True)
    
    # Obtener el usuario actual
    user_id = str(current_user.id)
    
    # Verificar que hay recursos
    if not recursos:
        flash('No se encontraron recursos en la base de datos', 'warning')
        recursos = []
    
    # Asegurar que todos los recursos tienen tags (incluso vacío)
    for recurso in recursos:
        if not recurso.get('tags'):
            recurso['tags'] = []
    
    return render_template('index.html', stats=stats, notes=list(notes), documents=list(documents), links=list(links), recursos=recursos, user_id=user_id)

@main.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        user = mongo.db.users.find_one({'email': email})
        if user and check_password_hash(user['password_hash'], password):
            user_obj = User(
                id=str(user['_id']),
                email=user['email'],
                password_hash=user['password_hash'],
                name=user['name'],
                role=user['role'],
                created_at=user['created_at'],
                last_login=datetime.now(),
                active=user['active'],
                avatar=user.get('avatar')
            )
            login_user(user_obj)
            mongo.db.users.update_one(
                {'_id': user['_id']},
                {'$set': {'last_login': datetime.now()}}
            )
            flash(f'¡Bienvenido, {user_obj.name}!', 'success')
            return redirect(url_for('main.index'))
        flash('Email o contraseña incorrectos', 'error')
    return render_template('login.html')

@main.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        name = request.form.get('name')
        
        if mongo.db.users.find_one({'email': email}):
            flash('Email ya registrado', 'error')
            return redirect(url_for('main.register'))
        
        # Crear nuevo usuario
        user = {
            'email': email,
            'password_hash': generate_password_hash(password),
            'name': name,
            'role': 'user',
            'created_at': datetime.now(),
            'last_login': datetime.now(),
            'active': True
        }
        result = mongo.db.users.insert_one(user)
        
        # Crear objeto User y loguear
        user_obj = User(
            id=str(result.inserted_id),
            email=email,
            password_hash=user['password_hash'],
            name=name,
            role='user',
            created_at=datetime.now(),
            last_login=datetime.now(),
            active=True
        )
        login_user(user_obj)
        flash('¡Registro exitoso!', 'success')
        return redirect(url_for('main.index'))
    return render_template('register.html')

@main.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Has cerrado sesión', 'success')
    return redirect(url_for('main.login'))

@main.route('/add_resource_form')
def add_resource_form():
    return render_template('add_resource.html')

@main.route('/add_resource', methods=['POST'])
@login_required
def add_resource():
    tipo = request.form.get('tipo')
    user_id = str(current_user.id)
    
    if tipo == 'documento':
        # Manejar subida de archivo
        if 'archivo' not in request.files:
            flash('No se seleccionó ningún archivo', 'error')
            return redirect(url_for('main.add_resource_form'))
            
        file = request.files['archivo']
        if file.filename == '':
            flash('No se seleccionó ningún archivo', 'error')
            return redirect(url_for('main.add_resource_form'))
            
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(current_app.config['UPLOAD_FOLDER'], filename))
            
            # Guardar en MongoDB
            documento = {
                'nombre': request.form.get('nombre'),
                'descripcion': request.form.get('descripcion'),
                'ruta_archivo': filename,
                'fecha_subida': datetime.now(LOCAL_TZ),
                'tags': request.form.get('tags', '').split(','),
                'user_id': user_id
            }
            mongo.db.documents.insert_one(documento)
            
            flash('Documento agregado exitosamente', 'success')
            return redirect(url_for('main.index'))
    
    elif tipo == 'enlace':
        url = request.form.get('url')
        if not validate_url(url):
            flash('URL no válida', 'error')
            return redirect(url_for('main.add_resource_form'))
            
        contenido = descargar_web(url)
        
        # Guardar en MongoDB
        enlace = {
            'url': url,
            'titulo': request.form.get('titulo'),
            'descripcion': contenido[:200] + '...',
            'fecha_creacion': datetime.now(LOCAL_TZ),
            'tags': request.form.get('tags', '').split(','),
            'user_id': user_id
        }
        mongo.db.links.insert_one(enlace)
        
        flash('Enlace agregado exitosamente', 'success')
        return redirect(url_for('main.index'))
    
    elif tipo == 'nota':
        # Guardar en MongoDB
        nota = {
            'titulo': request.form.get('titulo'),
            'descripcion': request.form.get('descripcion'),
            'contenido': request.form.get('contenido'),
            'fecha_creacion': datetime.now(LOCAL_TZ),
            'tags': request.form.get('tags', '').split(','),
            'user_id': user_id
        }
        mongo.db.notes.insert_one(nota)
        
        flash('Nota agregada exitosamente', 'success')
        return redirect(url_for('main.index'))
    
    flash('Tipo de recurso no válido', 'error')
    return redirect(url_for('main.add_resource_form'))

@main.route('/add_evento', methods=['POST'])
@login_required
def add_evento():
    titulo = request.form.get('titulo')
    fecha_hora = request.form.get('fecha_hora')
    descripcion = request.form.get('descripcion')
    user_id = str(current_user.id)
    
    if not titulo or not fecha_hora:
        flash('Título y fecha/hora son requeridos', 'error')
        return redirect(url_for('main.index'))
        
    try:
        fecha_hora = datetime.fromisoformat(fecha_hora.replace('T', ' '))
        fecha_hora = LOCAL_TZ.localize(fecha_hora)
        fecha_fin = fecha_hora + timedelta(hours=1)  # Añadir 1 hora a la fecha de inicio
    except ValueError:
        flash('Formato de fecha/hora inválido', 'error')
        return redirect(url_for('main.index'))
    
    # Crear evento usando el servicio
    calendar_service = CalendarService(mongo.db)
    calendar_service.create_event(
        title=titulo,
        description=descripcion,
        start_time=fecha_hora,
        end_time=fecha_fin,
        all_day=False,
        user_id=user_id
    )
    
    flash('Evento agregado exitosamente', 'success')
    return redirect(url_for('main.index'))

@main.route('/api/v1/calendar/events')
def get_calendar_events():
    """
    Obtiene eventos para el calendario
    """
    events = mongo.db.events.find()
    
    # Convertir eventos a formato compatible con FullCalendar
    calendar_events = []
    for event in events:
        calendar_events.append({
            'id': str(event.get('_id', '')),
            'title': event.get('title', ''),
            'start': event.get('start_time', datetime.now()).isoformat(),
            'end': event.get('end_time', datetime.now() + timedelta(hours=1)).isoformat(),
            'allDay': event.get('all_day', False)
        })
    
    return jsonify(calendar_events)

@main.route('/search')
def search():
    query = request.args.get('q', '')
    
    # Buscar en documentos
    documentos = mongo.db.documents.find({
        '$or': [
            {'nombre': {'$regex': query, '$options': 'i'}},
            {'descripcion': {'$regex': query, '$options': 'i'}},
            {'tags': {'$regex': query, '$options': 'i'}}
        ]
    })
    
    # Buscar en enlaces
    enlaces = mongo.db.links.find({
        '$or': [
            {'titulo': {'$regex': query, '$options': 'i'}},
            {'descripcion': {'$regex': query, '$options': 'i'}},
            {'tags': {'$regex': query, '$options': 'i'}}
        ]
    })
    
    return render_template('search.html', query=query, documentos=list(documentos), enlaces=list(enlaces))

@main.route('/edit_resource_form/<resource_id>')
def edit_resource_form(resource_id):
    # Buscar el recurso en documentos o enlaces
    documento = mongo.db.documents.find_one({'_id': ObjectId(resource_id)})
    enlace = mongo.db.links.find_one({'_id': ObjectId(resource_id)})
    
    if not documento and not enlace:
        flash('Recurso no encontrado', 'error')
        return redirect(url_for('main.index'))
    
    return render_template('edit_resource.html', documento=documento, enlace=enlace)

@main.route('/edit_resource/<resource_id>', methods=['POST'])
def edit_resource(resource_id):
    tipo = request.form.get('tipo')
    
    if tipo == 'documento':
        documento = mongo.db.documents.find_one({'_id': ObjectId(resource_id)})
        if not documento:
            flash('Documento no encontrado', 'error')
            return redirect(url_for('main.index'))
            
        # Actualizar documento
        mongo.db.documents.update_one(
            {'_id': ObjectId(resource_id)},
            {
                '$set': {
                    'nombre': request.form.get('nombre'),
                    'descripcion': request.form.get('descripcion'),
                    'tags': request.form.get('tags', '').split(',').strip(),
                    'fecha_actualizacion': datetime.now(LOCAL_TZ)
                }
            }
        )
        
        flash('Documento actualizado exitosamente', 'success')
        return redirect(url_for('main.index'))
    
    elif tipo == 'enlace':
        enlace = mongo.db.links.find_one({'_id': ObjectId(resource_id)})
        if not enlace:
            flash('Enlace no encontrado', 'error')
            return redirect(url_for('main.index'))
            
        # Actualizar enlace
        mongo.db.links.update_one(
            {'_id': ObjectId(resource_id)},
            {
                '$set': {
                    'titulo': request.form.get('titulo'),
                    'descripcion': request.form.get('descripcion'),
                    'tags': request.form.get('tags', '').split(',').strip(),
                    'fecha_actualizacion': datetime.now(LOCAL_TZ)
                }
            }
        )
        
        flash('Enlace actualizado exitosamente', 'success')
        return redirect(url_for('main.index'))
    
    flash('Tipo de recurso no válido', 'error')
    return redirect(url_for('main.index'))

@main.route('/delete_resource/<resource_id>')
def delete_resource(resource_id):
    # Intentar eliminar tanto en documentos como en enlaces
    resultado_doc = mongo.db.documents.delete_one({'_id': ObjectId(resource_id)})
    resultado_link = mongo.db.links.delete_one({'_id': ObjectId(resource_id)})
    
    if resultado_doc.deleted_count == 0 and resultado_link.deleted_count == 0:
        flash('Recurso no encontrado', 'error')
    else:
        flash('Recurso eliminado exitosamente', 'success')
    
    return redirect(url_for('main.index'))

@main.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(current_app.config['UPLOAD_FOLDER'], filename)
