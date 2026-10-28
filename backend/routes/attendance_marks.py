from datetime import date
import math
import re

from flask import Blueprint, request, jsonify
from database import db, Attendance, Mark, Assignment, Quiz, Student, Subject, Prediction
from auth_middleware import token_required
from ml.predict import predict_student_performance
import json

att_marks_bp = Blueprint('attendance_marks', __name__)


def _faculty_department_id(current_user):
    faculty = current_user.faculty_profile
    return faculty.department_id if faculty else None


def _valid_date(value):
    if not isinstance(value, str) or not re.fullmatch(r'\d{4}-\d{2}-\d{2}', value):
        return False
    try:
        date.fromisoformat(value)
        return True
    except ValueError:
        return False


def _positive_id(value):
    if isinstance(value, bool):
        raise ValueError
    parsed = int(value)
    if parsed <= 0 or (isinstance(value, float) and not value.is_integer()):
        raise ValueError
    return parsed


@att_marks_bp.route('/subjects', methods=['GET'])
@token_required(allowed_roles=['admin', 'faculty'])
def get_subjects(current_user):
    query = Subject.query
    if current_user.role == 'faculty':
        department_id = _faculty_department_id(current_user)
        if department_id is None:
            return jsonify({'subjects': []}), 200
        query = query.filter_by(department_id=department_id)

    subjects = query.order_by(Subject.id).all()
    return jsonify({'subjects': [{
        'id': subject.id,
        'code': subject.code,
        'name': subject.name,
        'department_id': subject.department_id,
        'semester': subject.semester
    } for subject in subjects]}), 200


# --- ATTENDANCE ROUTES ---
@att_marks_bp.route('/attendance', methods=['GET'])
@token_required()
def get_attendance(current_user):
    student_id = request.args.get('student_id', type=int)
    if current_user.role == 'student':
        student_id = current_user.student_profile.id if current_user.student_profile else None
        
    query = Attendance.query
    if current_user.role == 'student':
        if student_id is None:
            return jsonify({'attendance': []}), 200
        query = query.filter_by(student_id=student_id)
    elif current_user.role == 'faculty':
        department_id = _faculty_department_id(current_user)
        if department_id is None:
            return jsonify({'attendance': []}), 200
        query = query.join(Student).filter(Student.department_id == department_id)
        if student_id is not None:
            query = query.filter(Attendance.student_id == student_id)
    elif student_id is not None:
        query = query.filter_by(student_id=student_id)
        
    records = query.all()
    res = [{
        'id': r.id,
        'student_id': r.student_id,
        'student_name': r.student.user.name,
        'subject_code': r.subject.code,
        'subject_name': r.subject.name,
        'date': r.date,
        'status': r.status,
        'percentage': r.percentage
    } for r in records]
    
    return jsonify({'attendance': res}), 200

@att_marks_bp.route('/attendance', methods=['POST'])
@token_required(allowed_roles=['admin', 'faculty'])
def add_attendance(current_user):
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({'message': 'A JSON object is required.'}), 400
    try:
        student_id = _positive_id(data.get('student_id'))
        subject_id = _positive_id(data.get('subject_id'))
        percentage = float(data.get('percentage', 80.0))
    except (TypeError, ValueError, OverflowError):
        return jsonify({'message': 'Valid student_id, subject_id, and percentage are required.'}), 400

    status = data.get('status', 'Present')
    date_str = data.get('date')
    if status not in ('Present', 'Absent', 'Excused'):
        return jsonify({'message': 'status must be Present, Absent, or Excused.'}), 400
    if not math.isfinite(percentage) or not 0 <= percentage <= 100:
        return jsonify({'message': 'percentage must be between 0 and 100.'}), 400
    if not _valid_date(date_str):
        return jsonify({'message': 'date must be a valid ISO date (YYYY-MM-DD).'}), 400

    student = db.session.get(Student, student_id)
    subject = db.session.get(Subject, subject_id)
    if not student or not subject:
        return jsonify({'message': 'Student and subject must exist.'}), 404
    if student.department_id != subject.department_id:
        return jsonify({'message': 'Student and subject must belong to the same department.'}), 400
    if current_user.role == 'faculty' and student.department_id != _faculty_department_id(current_user):
        return jsonify({'message': 'You can only update students in your department.'}), 403
        
    att = Attendance(
        student_id=student_id,
        subject_id=subject_id,
        status=status,
        percentage=percentage,
        date=date_str
    )
    db.session.add(att)
    
    # Recalculate student ML prediction
    recalculate_student_prediction(student_id)
    db.session.commit()
    
    return jsonify({'message': 'Attendance record saved & student prediction updated.', 'id': att.id}), 201

# --- MARKS ROUTES ---
@att_marks_bp.route('/marks', methods=['GET'])
@token_required()
def get_marks(current_user):
    student_id = request.args.get('student_id', type=int)
    if current_user.role == 'student':
        student_id = current_user.student_profile.id if current_user.student_profile else None
        
    query = Mark.query
    if current_user.role == 'student':
        if student_id is None:
            return jsonify({'marks': []}), 200
        query = query.filter_by(student_id=student_id)
    elif current_user.role == 'faculty':
        department_id = _faculty_department_id(current_user)
        if department_id is None:
            return jsonify({'marks': []}), 200
        query = query.join(Student).filter(Student.department_id == department_id)
        if student_id is not None:
            query = query.filter(Mark.student_id == student_id)
    elif student_id is not None:
        query = query.filter_by(student_id=student_id)
        
    records = query.all()
    res = [{
        'id': r.id,
        'student_id': r.student_id,
        'student_name': r.student.user.name,
        'subject_code': r.subject.code,
        'subject_name': r.subject.name,
        'test_type': r.test_type,
        'score': r.score,
        'max_score': r.max_score,
        'date': r.date
    } for r in records]
    
    return jsonify({'marks': res}), 200

@att_marks_bp.route('/marks', methods=['POST'])
@token_required(allowed_roles=['admin', 'faculty'])
def add_mark(current_user):
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({'message': 'A JSON object is required.'}), 400
    try:
        student_id = _positive_id(data.get('student_id'))
        subject_id = _positive_id(data.get('subject_id'))
        score = float(data.get('score', 75.0))
        max_score = float(data.get('max_score', 100.0))
    except (TypeError, ValueError, OverflowError):
        return jsonify({'message': 'Valid student_id, subject_id, score, and max_score are required.'}), 400

    test_type = data.get('test_type', 'Unit Test')
    date_str = data.get('date')
    if not isinstance(test_type, str) or not test_type.strip() or len(test_type) > 50:
        return jsonify({'message': 'test_type must be a non-empty string of at most 50 characters.'}), 400
    if not math.isfinite(score) or not math.isfinite(max_score) or max_score <= 0 or not 0 <= score <= max_score:
        return jsonify({'message': 'score must be between 0 and a positive max_score.'}), 400
    if not _valid_date(date_str):
        return jsonify({'message': 'date must be a valid ISO date (YYYY-MM-DD).'}), 400

    student = db.session.get(Student, student_id)
    subject = db.session.get(Subject, subject_id)
    if not student or not subject:
        return jsonify({'message': 'Student and subject must exist.'}), 404
    if student.department_id != subject.department_id:
        return jsonify({'message': 'Student and subject must belong to the same department.'}), 400
    if current_user.role == 'faculty' and student.department_id != _faculty_department_id(current_user):
        return jsonify({'message': 'You can only update students in your department.'}), 403
        
    m = Mark(
        student_id=student_id,
        subject_id=subject_id,
        test_type=test_type,
        score=score,
        max_score=max_score,
        date=date_str
    )
    db.session.add(m)
    
    recalculate_student_prediction(student_id)
    db.session.commit()
    
    return jsonify({'message': 'Mark entry recorded & student prediction refreshed.', 'id': m.id}), 201

# Helper function to trigger auto-recalculation of ML prediction for a student
def recalculate_student_prediction(student_id):
    student = Student.query.get(student_id)
    if not student:
        return
        
    attendances = Attendance.query.filter_by(student_id=student_id).all()
    marks = Mark.query.filter_by(student_id=student_id).all()
    assignments = Assignment.query.filter_by(student_id=student_id).all()
    quizzes = Quiz.query.filter_by(student_id=student_id).all()
    
    avg_att = sum(a.percentage for a in attendances) / len(attendances) if attendances else 75.0
    avg_mks = sum(m.score for m in marks) / len(marks) if marks else 65.0
    avg_asg = sum(a.score for a in assignments) / len(assignments) if assignments else 70.0
    avg_qz = sum(q.score for q in quizzes) / len(quizzes) if quizzes else 65.0
    recent_mks = marks[-1].score if marks else avg_mks
    
    ml_data = {
        'attendance': float(avg_att),
        'internal_marks': float(avg_mks),
        'assignment_score': float(avg_asg),
        'quiz_score': float(avg_qz),
        'study_hours': float(student.study_hours),
        'prev_gpa': float(student.prev_gpa),
        'prev_sem_score': float(student.prev_gpa * 9.5),
        'assignment_completion': float(avg_asg),
        'participation': float(student.participation),
        'backlogs': int(student.backlogs),
        'recent_test_score': float(recent_mks)
    }
    
    pred_res = predict_student_performance(ml_data)
    
    pred_obj = Prediction(
        student_id=student.id,
        predicted_score=pred_res['predicted_score'],
        performance_category=pred_res['performance_category'],
        risk_level=pred_res['risk_level'],
        confidence=pred_res['confidence'],
        shap_explanation=json.dumps(pred_res['xai']),
        model_used=pred_res['model_used']
    )
    db.session.add(pred_obj)
