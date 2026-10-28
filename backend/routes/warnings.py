from flask import Blueprint, request, jsonify
from database import db, RiskAlert, Student
from auth_middleware import token_required

warnings_bp = Blueprint('warnings', __name__)

@warnings_bp.route('', methods=['GET'])
@token_required()
def get_warnings(current_user):
    risk_level = request.args.get('risk_level')
    status = request.args.get('status', 'Active')
    
    query = RiskAlert.query.join(Student)
    
    if current_user.role == 'student':
        if current_user.student_profile:
            query = query.filter(RiskAlert.student_id == current_user.student_profile.id)
        else:
            return jsonify({'alerts': []}), 200
    elif current_user.role == 'faculty':
        faculty = current_user.faculty_profile
        if not faculty:
            return jsonify({'alerts': []}), 200
        query = query.filter(Student.department_id == faculty.department_id)
            
    if risk_level:
        query = query.filter(RiskAlert.risk_level == risk_level)
    if status and status != 'All':
        query = query.filter(RiskAlert.status == status)
        
    alerts = query.all()
    
    res = [{
        'id': a.id,
        'student_id': a.student_id,
        'student_name': a.student.user.name,
        'student_code': a.student.student_code,
        'department_name': a.student.department.name,
        'warning_type': a.warning_type,
        'risk_level': a.risk_level,
        'message': a.message,
        'status': a.status,
        'created_at': str(a.created_at)
    } for a in alerts]
    
    return jsonify({'alerts': res}), 200

@warnings_bp.route('/<int:alert_id>/resolve', methods=['POST'])
@token_required(allowed_roles=['admin', 'faculty'])
def resolve_warning(current_user, alert_id):
    alert = RiskAlert.query.get_or_404(alert_id)
    if current_user.role == 'faculty':
        faculty = current_user.faculty_profile
        if not faculty or alert.student.department_id != faculty.department_id:
            return jsonify({'message': 'You can only resolve alerts for students in your department.'}), 403
    alert.status = 'Resolved'
    db.session.commit()
    return jsonify({'message': f'Risk alert #{alert_id} marked as Resolved.'}), 200
