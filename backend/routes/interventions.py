from datetime import date, timedelta
from flask import Blueprint, request, jsonify
from database import db, Intervention, Student, Faculty
from auth_middleware import token_required
from services.notifications import queue_notification

interventions_bp = Blueprint('interventions', __name__)

@interventions_bp.route('', methods=['GET'])
@token_required()
def get_interventions(current_user):
    student_id = request.args.get('student_id', type=int)
    
    query = Intervention.query
    if current_user.role == 'student':
        if current_user.student_profile:
            query = query.filter_by(student_id=current_user.student_profile.id)
        else:
            return jsonify({'interventions': []}), 200
    elif current_user.role == 'faculty':
        faculty = current_user.faculty_profile
        if not faculty:
            return jsonify({'interventions': []}), 200
        query = query.join(Student).filter(Student.department_id == faculty.department_id)
        if student_id is not None:
            query = query.filter(Intervention.student_id == student_id)
    elif student_id:
        query = query.filter_by(student_id=student_id)
        
    items = query.order_by(Intervention.date.desc()).all()
    
    res = [{
        'id': i.id,
        'student_id': i.student_id,
        'student_name': i.student.user.name,
        'student_code': i.student.student_code,
        'faculty_id': i.faculty_id,
        'faculty_name': i.faculty.user.name,
        'type': i.type,
        'notes': i.notes,
        'date': i.date,
        'student_response': i.student_response,
        'next_review_date': i.next_review_date,
        'status': i.status
    } for i in items]
    
    return jsonify({'interventions': res}), 200

@interventions_bp.route('', methods=['POST'])
@token_required(allowed_roles=['admin', 'faculty'])
def create_intervention(current_user):
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({'message': 'A JSON object is required.'}), 400
    student_id = data.get('student_id')
    inv_type = data.get('type', 'Academic Counseling')
    notes = data.get('notes', '')
    # Bug fix: defaults were hardcoded to '2026-09-18' / '2026-10-02' - now dynamic
    date_str = data.get('date', date.today().isoformat())
    response = data.get('student_response', '')
    next_review = data.get('next_review_date', (date.today() + timedelta(days=14)).isoformat())
    
    if not student_id:
        return jsonify({'message': 'student_id is required.'}), 400

    try:
        student_id = int(student_id)
    except (TypeError, ValueError, OverflowError):
        return jsonify({'message': 'student_id must be a valid ID.'}), 400
    # Bug fix: replaced deprecated Student.query.get() with db.session.get()
    student = db.session.get(Student, student_id)
    if not student:
        return jsonify({'message': 'Student not found.'}), 404

    if current_user.role == 'faculty':
        faculty_profile = current_user.faculty_profile
        if not faculty_profile:
            return jsonify({'message': 'Faculty profile is not available.'}), 403
        if faculty_profile.department_id != student.department_id:
            return jsonify({'message': 'You can only create interventions for students in your department.'}), 403
        faculty_id = faculty_profile.id
    else:
        try:
            faculty_id = int(data.get('faculty_id'))
        except (TypeError, ValueError, OverflowError):
            return jsonify({'message': 'A valid faculty_id is required for admin-created interventions.'}), 400
        # Bug fix: replaced deprecated Faculty.query.get() with db.session.get()
        faculty_profile = db.session.get(Faculty, faculty_id)
        if not faculty_profile:
            return jsonify({'message': 'Faculty profile not found.'}), 404
        if faculty_profile.department_id != student.department_id:
            return jsonify({'message': 'faculty_id must belong to the target student department.'}), 400

    inv = Intervention(
        student_id=student_id,
        faculty_id=faculty_id,
        type=inv_type,
        notes=notes,
        date=date_str,
        student_response=response,
        next_review_date=next_review,
        status='In Progress'
    )
    db.session.add(inv)
    queue_notification(
        student.user_id,
        f'New message from {current_user.name}',
        notes or f'{current_user.name} created an intervention: {inv_type}.',
        'message'
    )
    db.session.commit()
    
    return jsonify({'message': 'Intervention record created successfully.', 'id': inv.id}), 201
