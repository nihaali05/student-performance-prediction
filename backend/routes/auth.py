from flask import Blueprint, request, jsonify
from werkzeug.security import check_password_hash
from database import db, User, AuditLog
from auth_middleware import generate_token, token_required

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json() or {}
    email = data.get('email', '').strip()
    password = data.get('password', '').strip()
    
    if not email or not password:
        return jsonify({'message': 'Email and password are required.'}), 400
        
    user = User.query.filter_by(email=email).first()
    if not user or not check_password_hash(user.password_hash, password):
        return jsonify({'message': 'Invalid credentials. Please check your email and password.'}), 401
        
    token = generate_token(user)
    
    # Audit log
    log = AuditLog(user_id=user.id, action="USER_LOGIN", details=f"User {user.email} logged in with role {user.role}.")
    db.session.add(log)
    db.session.commit()
    
    student_id = user.student_profile.id if user.student_profile else None
    faculty_id = user.faculty_profile.id if user.faculty_profile else None
    
    return jsonify({
        'token': token,
        'user': {
            'id': user.id,
            'name': user.name,
            'email': user.email,
            'role': user.role,
            'department_id': user.department_id,
            'student_id': student_id,
            'faculty_id': faculty_id
        }
    }), 200

@auth_bp.route('/me', methods=['GET'])
@token_required()
def me(current_user):
    student_id = current_user.student_profile.id if current_user.student_profile else None
    faculty_id = current_user.faculty_profile.id if current_user.faculty_profile else None
    
    return jsonify({
        'user': {
            'id': current_user.id,
            'name': current_user.name,
            'email': current_user.email,
            'role': current_user.role,
            'department_id': current_user.department_id,
            'student_id': student_id,
            'faculty_id': faculty_id
        }
    }), 200
