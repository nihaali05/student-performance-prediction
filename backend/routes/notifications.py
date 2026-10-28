from flask import Blueprint, jsonify, request

from auth_middleware import token_required
from database import db, Faculty, Notification, Student, User

notifications_bp = Blueprint('notifications', __name__)


def serialize_notification(notification):
    return {
        'id': notification.id,
        'title': notification.title,
        'message': notification.message,
        'type': notification.type,
        'is_read': notification.is_read,
        'created_at': notification.created_at.isoformat()
    }


@notifications_bp.route('', methods=['GET'])
@token_required()
def get_notifications(current_user):
    query = Notification.query.filter_by(user_id=current_user.id)
    unread_count = query.filter_by(is_read=False).count()
    notifications = query.order_by(Notification.created_at.desc()).limit(50).all()
    return jsonify({
        'notifications': [serialize_notification(item) for item in notifications],
        'unread_count': unread_count
    }), 200


@notifications_bp.route('/contacts', methods=['GET'])
@token_required(allowed_roles=['student', 'faculty'])
def get_notification_contacts(current_user):
    if current_user.role == 'student':
        if not current_user.student_profile:
            return jsonify({'message': 'Student profile is not available.'}), 404
        users = User.query.join(
            Faculty, Faculty.user_id == User.id
        ).filter(
            Faculty.department_id == current_user.student_profile.department_id
        ).order_by(User.name).all()
    else:
        if not current_user.faculty_profile:
            return jsonify({'message': 'Faculty profile is not available.'}), 404
        users = User.query.join(
            Student, Student.user_id == User.id
        ).filter(
            Student.department_id == current_user.faculty_profile.department_id
        ).order_by(User.name).all()

    return jsonify({
        'contacts': [
            {'id': user.id, 'name': user.name, 'role': user.role}
            for user in users
        ]
    }), 200


@notifications_bp.route('/message', methods=['POST'])
@token_required(allowed_roles=['student', 'faculty'])
def send_message(current_user):
    data = request.get_json() or {}
    recipient_id = data.get('recipient_user_id')
    message = data.get('message')

    if (
        not isinstance(recipient_id, int)
        or isinstance(recipient_id, bool)
        or recipient_id < 1
        or not isinstance(message, str)
        or not message.strip()
    ):
        return jsonify({'message': 'A recipient and message are required.'}), 400
    message = message.strip()
    if len(message) > 5000:
        return jsonify({'message': 'Messages cannot exceed 5000 characters.'}), 400

    # Bug fix: replaced deprecated .query.get() with db.session.get()
    recipient = db.session.get(User, recipient_id)
    if not recipient:
        return jsonify({'message': 'The selected recipient does not exist.'}), 404

    if current_user.role == 'student':
        sender_profile = current_user.student_profile
        recipient_profile = recipient.faculty_profile
        expected_role = 'faculty'
    else:
        sender_profile = current_user.faculty_profile
        recipient_profile = recipient.student_profile
        expected_role = 'student'

    if not sender_profile:
        return jsonify({'message': f'{current_user.role.capitalize()} profile is not available.'}), 403
    if recipient.role != expected_role or not recipient_profile:
        return jsonify({'message': f'Messages can only be sent to {expected_role}s.'}), 403
    if sender_profile.department_id != recipient_profile.department_id:
        return jsonify({'message': 'Messages are limited to your department.'}), 403

    db.session.add(Notification(
        user_id=recipient.id,
        title=f'Message from {current_user.name}',
        message=message,
        type='message'
    ))
    db.session.commit()

    return jsonify({'message': 'Message sent successfully.'}), 201


@notifications_bp.route('/<int:notification_id>/read', methods=['POST'])
@token_required()
def mark_notification_read(current_user, notification_id):
    notification = Notification.query.filter_by(
        id=notification_id,
        user_id=current_user.id
    ).first_or_404()
    notification.is_read = True
    db.session.commit()
    return jsonify({'message': 'Notification marked as read.'}), 200


@notifications_bp.route('/read-all', methods=['POST'])
@token_required()
def mark_all_notifications_read(current_user):
    Notification.query.filter_by(
        user_id=current_user.id,
        is_read=False
    ).update({'is_read': True})
    db.session.commit()
    return jsonify({'message': 'All notifications marked as read.'}), 200
