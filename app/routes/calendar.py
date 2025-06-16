from flask import Blueprint, jsonify, request
from ..utils import token_required
from ..services import CalendarService

calendar = Blueprint('calendar', __name__, url_prefix='/api/v1/calendar')

@calendar.route('/events', methods=['POST'])
@token_required
def create_event(current_user):
    """
    Crea un nuevo evento
    """
    data = request.get_json()
    try:
        event = calendar_service.create_event(
            title=data['title'],
            description=data['description'],
            start_time=data['start_time'],
            end_time=data['end_time'],
            all_day=data.get('all_day', False),
            location=data.get('location'),
            category=data.get('category'),
            user_id=current_user['_id']
        )
        return jsonify(event), 201
    except ValueError as e:
        return jsonify({'error': str(e)}), 400

@calendar.route('/events', methods=['GET'])
@token_required
def get_events(current_user):
    """
    Obtiene eventos del usuario
    """
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    category = request.args.get('category')
    
    events = calendar_service.get_events(
        user_id=current_user['_id'],
        start_date=start_date,
        end_date=end_date,
        category=category
    )
    return jsonify(events)

@calendar.route('/events/<event_id>', methods=['PUT'])
@token_required
def update_event(current_user, event_id):
    """
    Actualiza un evento
    """
    data = request.get_json()
    try:
        event = calendar_service.update_event(
            event_id=event_id,
            user_id=current_user['_id'],
            title=data['title'],
            description=data['description'],
            start_time=data['start_time'],
            end_time=data['end_time'],
            all_day=data.get('all_day', False),
            location=data.get('location'),
            category=data.get('category')
        )
        return jsonify(event)
    except ValueError as e:
        return jsonify({'error': str(e)}), 400

@calendar.route('/events/<event_id>', methods=['DELETE'])
@token_required
def delete_event(current_user, event_id):
    """
    Elimina un evento
    """
    try:
        if calendar_service.delete_event(event_id, current_user['_id']):
            return '', 204
        return jsonify({'error': 'Evento no encontrado'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@calendar.route('/events/upcoming', methods=['GET'])
@token_required
def get_upcoming_events(current_user):
    """
    Obtiene eventos próximos
    """
    days = request.args.get('days', 7, type=int)
    events = calendar_service.get_upcoming_events(
        user_id=current_user['_id'],
        days=days
    )
    return jsonify(events)

@calendar.route('/reminders', methods=['POST'])
@token_required
def create_reminder(current_user):
    """
    Crea un recordatorio para un evento
    """
    data = request.get_json()
    try:
        reminder = calendar_service.create_reminder(
            event_id=data['event_id'],
            user_id=current_user['_id'],
            time_before=data['time_before'],
            notification_type=data['notification_type']
        )
        return jsonify(reminder), 201
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
