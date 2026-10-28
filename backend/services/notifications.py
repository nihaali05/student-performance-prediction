from database import db, Notification, User


def queue_notification(user_id, title, message, notification_type='info'):
    db.session.add(Notification(
        user_id=user_id,
        title=title,
        message=message,
        type=notification_type
    ))


def queue_department_notifications(department_id, role, title, message, notification_type='info'):
    recipients = User.query.filter_by(
        department_id=department_id,
        role=role
    ).all()
    for recipient in recipients:
        queue_notification(recipient.id, title, message, notification_type)
