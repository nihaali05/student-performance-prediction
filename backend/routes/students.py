import json
from flask import Blueprint, request, jsonify
from database import db, Student, User, Department, Prediction, Attendance, Mark, Assignment, Quiz, RiskAlert, Intervention
from auth_middleware import token_required
from ml.predict import predict_student_performance

students_bp = Blueprint('students', __name__)

@students_bp.route('', methods=['GET'])
@token_required(allowed_roles=['admin', 'faculty'])
def get_students(current_user):
    department_id = request.args.get('department_id', type=int)
    risk_level = request.args.get('risk_level')
    search = request.args.get('search', '').strip()
    
    query = Student.query.join(User).join(Department)

    if current_user.role == 'faculty':
        faculty = current_user.faculty_profile
        faculty_department_id = (
            faculty.department_id if faculty else current_user.department_id
        )
        if faculty_department_id is None:
            query = query.filter(Student.id == -1)
        else:
            query = query.filter(Student.department_id == faculty_department_id)
    
    if department_id:
        query = query.filter(Student.department_id == department_id)
        
    if search:
        query = query.filter(User.name.ilike(f'%{search}%') | Student.student_code.ilike(f'%{search}%'))
        
    students_list = query.all()
    
    result = []
    for s in students_list:
        latest_pred = Prediction.query.filter_by(student_id=s.id).order_by(Prediction.created_at.desc()).first()
        
        # Filter by risk level if requested
        current_risk = latest_pred.risk_level if latest_pred else 'GREEN'
        if risk_level and current_risk != risk_level:
            continue
            
        result.append({
            'id': s.id,
            'user_id': s.user_id,
            'name': s.user.name,
            'email': s.user.email,
            'student_code': s.student_code,
            'department_id': s.department_id,
            'department_name': s.department.name,
            'department_code': s.department.code,
            'semester': s.semester,
            'section': s.section,
            'gpa': s.gpa,
            'prev_gpa': s.prev_gpa,
            'study_hours': s.study_hours,
            'backlogs': s.backlogs,
            'participation': s.participation,
            'predicted_score': latest_pred.predicted_score if latest_pred else None,
            'performance_category': latest_pred.performance_category if latest_pred else 'N/A',
            'risk_level': current_risk,
            'confidence': latest_pred.confidence if latest_pred else None
        })
        
    return jsonify({'students': result, 'total': len(result)}), 200

@students_bp.route('/<int:student_id>', methods=['GET'])
@token_required()
def get_student_detail(current_user, student_id):
    # Authorization check: Student can only view their own profile
    if current_user.role == 'student' and (not current_user.student_profile or current_user.student_profile.id != student_id):
        return jsonify({'message': 'Unauthorized to view another student profile.'}), 403
        
    student = Student.query.get_or_404(student_id)
    if current_user.role == 'faculty':
        faculty = current_user.faculty_profile
        faculty_department_id = (
            faculty.department_id if faculty else current_user.department_id
        )
        if faculty_department_id is None or student.department_id != faculty_department_id:
            return jsonify({'message': 'Unauthorized to view students outside your department.'}), 403
    
    latest_pred = Prediction.query.filter_by(student_id=student.id).order_by(Prediction.created_at.desc()).first()
    shap_data = json.loads(latest_pred.shap_explanation) if (latest_pred and latest_pred.shap_explanation) else None
    
    attendances = Attendance.query.filter_by(student_id=student.id).all()
    marks = Mark.query.filter_by(student_id=student.id).all()
    assignments = Assignment.query.filter_by(student_id=student.id).all()
    quizzes = Quiz.query.filter_by(student_id=student.id).all()
    alerts = RiskAlert.query.filter_by(student_id=student.id).all()
    interventions = Intervention.query.filter_by(student_id=student.id).all()
    
    # Calculate summary metrics
    avg_attendance = sum(a.percentage for a in attendances) / len(attendances) if attendances else 75.0
    avg_marks = sum(m.score for m in marks) / len(marks) if marks else 65.0
    avg_assignments = sum(a.score for a in assignments) / len(assignments) if assignments else 70.0
    avg_quizzes = sum(q.score for q in quizzes) / len(quizzes) if quizzes else 65.0
    
    return jsonify({
        'student': {
            'id': student.id,
            'user_id': student.user_id,
            'name': student.user.name,
            'email': student.user.email,
            'student_code': student.student_code,
            'department_name': student.department.name,
            'semester': student.semester,
            'section': student.section,
            'gpa': student.gpa,
            'prev_gpa': student.prev_gpa,
            'study_hours': student.study_hours,
            'backlogs': student.backlogs,
            'participation': student.participation,
            'avg_attendance': round(avg_attendance, 1),
            'avg_marks': round(avg_marks, 1),
            'avg_assignments': round(avg_assignments, 1),
            'avg_quizzes': round(avg_quizzes, 1)
        },
        'prediction': {
            'predicted_score': latest_pred.predicted_score if latest_pred else 70.0,
            'performance_category': latest_pred.performance_category if latest_pred else 'Average Performer',
            'risk_level': latest_pred.risk_level if latest_pred else 'GREEN',
            'confidence': latest_pred.confidence if latest_pred else 85.0,
            'model_used': latest_pred.model_used if latest_pred else 'Linear Regression',
            'xai': shap_data
        },
        'attendance_history': [{'id': a.id, 'subject_name': a.subject.name, 'date': a.date, 'status': a.status, 'percentage': a.percentage} for a in attendances],
        'marks_history': [{'id': m.id, 'subject_name': m.subject.name, 'test_type': m.test_type, 'score': m.score, 'max_score': m.max_score, 'date': m.date} for m in marks],
        'assignments_history': [{'id': a.id, 'subject_name': a.subject.name, 'title': a.title, 'score': a.score, 'submitted': a.submitted, 'date': a.date} for a in assignments],
        'quizzes_history': [{'id': q.id, 'subject_name': q.subject.name, 'title': q.title, 'score': q.score, 'date': q.date} for q in quizzes],
        'alerts': [{'id': a.id, 'type': a.warning_type, 'risk_level': a.risk_level, 'message': a.message, 'status': a.status, 'created_at': str(a.created_at)} for a in alerts],
        'interventions': [{'id': i.id, 'faculty_name': i.faculty.user.name, 'type': i.type, 'notes': i.notes, 'date': i.date, 'response': i.student_response, 'status': i.status} for i in interventions]
    }), 200

@students_bp.route('', methods=['POST'])
@token_required(allowed_roles=['admin', 'faculty'])
def create_student(current_user):
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({'message': 'A JSON object is required.'}), 400
    
    # Validation
    required = ['name', 'email', 'student_code', 'department_id']
    if any(k not in data for k in required):
        return jsonify({'message': 'Missing required student fields.'}), 400

    try:
        department_id = int(data['department_id'])
    except (TypeError, ValueError, OverflowError):
        return jsonify({'message': 'department_id must be a valid department ID.'}), 400
    department = Department.query.get(department_id)
    if not department:
        return jsonify({'message': 'Department not found.'}), 404
    if current_user.role == 'faculty':
        faculty = current_user.faculty_profile
        if not faculty:
            return jsonify({'message': 'Faculty profile is not available.'}), 403
        if faculty.department_id != department_id:
            return jsonify({'message': 'Faculty may only create students in their department.'}), 403

    name = data.get('name')
    email = data.get('email')
    student_code = data.get('student_code')
    if not all(isinstance(value, str) and value.strip() for value in (name, email, student_code)):
        return jsonify({'message': 'name, email, and student_code must be non-empty strings.'}), 400
    if User.query.filter_by(email=email.strip()).first():
        return jsonify({'message': 'A user with this email already exists.'}), 400
    if Student.query.filter_by(student_code=student_code.strip()).first():
        return jsonify({'message': 'A student with this student_code already exists.'}), 400
        
    from werkzeug.security import generate_password_hash
    u = User(
        name=name.strip(),
        email=email.strip(),
        password_hash=generate_password_hash(data.get('password', 'student123')),
        role='student',
        department_id=department_id
    )
    db.session.add(u)
    
    s = Student(
        user=u,
        student_code=student_code.strip(),
        department_id=department_id,
        semester=data.get('semester', 1),
        section=data.get('section', 'A'),
        gpa=data.get('gpa', 7.0),
        prev_gpa=data.get('prev_gpa', 7.0),
        study_hours=data.get('study_hours', 10.0),
        backlogs=data.get('backlogs', 0),
        participation=data.get('participation', 70.0)
    )
    db.session.add(s)
    
    try:
        db.session.flush()
        # Run initial prediction before committing any of the new records.
        ml_data = {
            'attendance': float(data.get('attendance', 75.0)),
            'internal_marks': float(data.get('internal_marks', 65.0)),
            'assignment_score': float(data.get('assignment_score', 70.0)),
            'quiz_score': float(data.get('quiz_score', 65.0)),
            'study_hours': float(data.get('study_hours', 10.0)),
            'prev_gpa': float(data.get('prev_gpa', 7.0)),
            'prev_sem_score': float(data.get('prev_sem_score', 68.0)),
            'assignment_completion': float(data.get('assignment_completion', 75.0)),
            'participation': float(data.get('participation', 70.0)),
            'backlogs': int(data.get('backlogs', 0)),
            'recent_test_score': float(data.get('recent_test_score', 65.0))
        }

        pred_res = predict_student_performance(ml_data)
        pred_obj = Prediction(
            student_id=s.id,
            predicted_score=pred_res['predicted_score'],
            performance_category=pred_res['performance_category'],
            risk_level=pred_res['risk_level'],
            confidence=pred_res['confidence'],
            shap_explanation=json.dumps(pred_res['xai']),
            model_used=pred_res['model_used']
        )
        db.session.add(pred_obj)
        db.session.commit()
    except (TypeError, ValueError, OverflowError):
        db.session.rollback()
        return jsonify({'message': 'Student metrics must contain valid numeric values.'}), 400
    except Exception:
        db.session.rollback()
        raise
    
    return jsonify({'message': 'Student created successfully.', 'student_id': s.id}), 201
