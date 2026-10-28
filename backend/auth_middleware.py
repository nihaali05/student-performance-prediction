import jwt
from datetime import datetime, timezone, timedelta
from functools import wraps
from flask import request, jsonify, current_app
from database import db, User

def generate_token(user):
    payload = {
        'id': user.id,
        'email': user.email,
        'role': user.role,
        'name': user.name,
        'department_id': user.department_id,
        # Bug fix: tokens previously had no expiry (lived forever). Now expire in 24 hrs.
        'exp': datetime.now(timezone.utc) + timedelta(hours=24),
        'iat': datetime.now(timezone.utc)
    }
    return jwt.encode(payload, current_app.config['JWT_SECRET_KEY'], algorithm='HS256')

def token_required(allowed_roles=None):
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            token = None
            if 'Authorization' in request.headers:
                auth_header = request.headers['Authorization']
                if auth_header.startswith('Bearer '):
                    token = auth_header.split(' ')[1]
                    
            if not token:
                return jsonify({'message': 'Authorization token is missing!'}), 401
                
            try:
                data = jwt.decode(token, current_app.config['JWT_SECRET_KEY'], algorithms=['HS256'])
                # Bug fix: replaced deprecated .query.get() with modern db.session.get()
                current_user = db.session.get(User, data['id'])
                if not current_user:
                    return jsonify({'message': 'User no longer exists!'}), 401
                    
                if allowed_roles and current_user.role not in allowed_roles:
                    return jsonify({'message': f'Unauthorized access. Role {current_user.role} insufficient.'}), 403
                    
            except jwt.ExpiredSignatureError:
                return jsonify({'message': 'Token has expired!'}), 401
            except Exception as e:
                return jsonify({'message': f'Invalid token: {str(e)}'}), 401
                
            return f(current_user, *args, **kwargs)
        return decorated
    return decorator
