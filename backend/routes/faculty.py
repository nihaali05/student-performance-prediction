from flask import Blueprint, request, jsonify
from database import db, Faculty, User, Department, Student, Prediction, Attendance, Mark
from auth_middleware import token_required
from werkzeug.security import generate_password_hash

faculty_bp = Blueprint('faculty', __name__)

@faculty_bp.route('', methods=['GET'])
@token_required(allowed_roles=['admin'])
def get_faculty_list(current_user):
    faculties = Faculty.query.join(User).join(Department).all()
    res = []
    for f in faculties:
        res.append({
            'id': f.id,
            'user_id': f.user_id,
            'name': f.user.name,
            'email': f.user.email,
            'employee_id': f.employee_id,
            'department_id': f.department_id,
            'department_name': f.department.name,
            'phone': f.phone
        })
    return jsonify({'faculty': res}), 200

@faculty_bp.route('', methods=['POST'])
@token_required(allowed_roles=['admin'])
def create_faculty(current_user):
    data = request.get_json() or {}
    required = ['name', 'email', 'employee_id', 'department_id']
    if any(k not in data for k in required):
        return jsonify({'message': 'Missing required faculty parameters.'}), 400
        
    u = User(
        name=data['name'],
        email=data['email'],
        password_hash=generate_password_hash(data.get('password', 'faculty123')),
        role='faculty',
        department_id=data['department_id']
    )
    db.session.add(u)
    db.session.commit()
    
    f = Faculty(
        user_id=u.id,
        department_id=data['department_id'],
        employee_id=data['employee_id'],
        phone=data.get('phone', '')
    )
    db.session.add(f)
    db.session.commit()
    
    return jsonify({'message': 'Faculty member created successfully.', 'id': f.id}), 201

@faculty_bp.route('/dashboard', methods=['GET'])
@token_required(allowed_roles=['faculty'])
def faculty_dashboard_stats(current_user):
    faculty = current_user.faculty_profile
    dept_id = faculty.department_id if faculty else current_user.department_id
    
    # Students in department
    students = Student.query.filter_by(department_id=dept_id).all()
    total_assigned = len(students)
    
    at_risk_count = 0
    high_risk_count = 0
    total_score_sum = 0
    valid_predictions = 0
    
    for s in students:
        pred = Prediction.query.filter_by(student_id=s.id).order_by(Prediction.created_at.desc()).first()
        if pred:
            total_score_sum += pred.predicted_score
            valid_predictions += 1
            if pred.risk_level in ['RED']:
                high_risk_count += 1
            elif pred.risk_level in ['ORANGE', 'YELLOW']:
                at_risk_count += 1
                
    avg_class_performance = round(total_score_sum / valid_predictions, 1) if valid_predictions > 0 else 72.5
    
    # Calculate overall class attendance
    attendances = Attendance.query.join(Student).filter(Student.department_id == dept_id).all()
    avg_attendance = round(sum(a.percentage for a in attendances) / len(attendances), 1) if attendances else 78.4
    
    return jsonify({
        'total_assigned_students': total_assigned,
        'avg_class_performance': avg_class_performance,
        'avg_attendance': avg_attendance,
        'at_risk_count': at_risk_count,
        'high_risk_count': high_risk_count,
        'department_name': faculty.department.name if faculty else "General"
    }), 200
