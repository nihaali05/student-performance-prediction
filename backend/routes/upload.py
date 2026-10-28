import os
import io
from datetime import date as today_date
import pandas as pd
from flask import Blueprint, request, jsonify, current_app
from werkzeug.utils import secure_filename
from database import db, Student, Subject, User, Attendance, Mark, Prediction
from auth_middleware import token_required
from services.notifications import queue_notification
from ml.predict import predict_student_performance
import json

upload_bp = Blueprint('upload', __name__)

@upload_bp.route('/csv', methods=['POST'])
@token_required(allowed_roles=['admin', 'faculty'])
def upload_csv(current_user):
    if 'file' not in request.files:
        return jsonify({'message': 'No file part in request.'}), 400
        
    file = request.files['file']
    if file.filename == '':
        return jsonify({'message': 'No file selected.'}), 400
        
    filename = secure_filename(file.filename)
    try:
        file_contents = file.read()
        if filename.lower().endswith('.csv'):
            df = pd.read_csv(io.BytesIO(file_contents))
        elif filename.lower().endswith(('.xls', '.xlsx')):
            df = pd.read_excel(io.BytesIO(file_contents))
        else:
            return jsonify({'message': 'Unsupported file format. Upload CSV or Excel file.'}), 400
        if 'student_code' not in df.columns:
            return jsonify({'message': 'The upload must include a student_code column.'}), 400

        faculty_department_id = None
        if current_user.role == 'faculty':
            faculty = current_user.faculty_profile
            if not faculty:
                return jsonify({'message': 'Faculty profile is not available.'}), 403
            faculty_department_id = faculty.department_id

        # Check every matched student before writing the upload or changing records.
        student_codes = {
            str(value).strip()
            for value in df['student_code'].tolist()
            if str(value).strip()
        }
        if not student_codes:
            return jsonify({'message': 'The upload must include at least one student_code.'}), 400
        if faculty_department_id is not None and student_codes:
            out_of_scope = Student.query.filter(
                Student.student_code.in_(student_codes),
                Student.department_id != faculty_department_id
            ).first()
            if out_of_scope:
                return jsonify({
                    'message': 'Upload contains students outside your department.'
                }), 403

        students_by_code = {
            student.student_code: student
            for student in Student.query.filter(Student.student_code.in_(student_codes)).all()
        }
        if not students_by_code:
            return jsonify({'message': 'No uploaded student_code matched a student record.'}), 400

        subject_by_student = {}
        if 'attendance' in df.columns or 'internal_marks' in df.columns:
            missing_subject_students = []
            for student in students_by_code.values():
                subject = Subject.query.filter_by(
                    department_id=student.department_id,
                    semester=student.semester
                ).order_by(Subject.id).first()
                if subject:
                    subject_by_student[student.id] = subject
                else:
                    missing_subject_students.append(student.student_code)
            if missing_subject_students:
                return jsonify({
                    'message': (
                        'No subject matches the department and semester for: '
                        + ', '.join(sorted(missing_subject_students))
                        + '. Add a compatible subject or remove attendance/mark columns.'
                    )
                }), 400

        os.makedirs(current_app.config['UPLOAD_FOLDER'], exist_ok=True)
        filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
        with open(filepath, 'wb') as upload_file:
            upload_file.write(file_contents)
            
        processed_count = 0
        updated_predictions = 0
        
        # Expected column headers: student_code, attendance, internal_marks, assignment_score, quiz_score, study_hours
        for _, row in df.iterrows():
            student_code = str(row.get('student_code', '')).strip()
            if not student_code:
                continue
                
            student = students_by_code.get(student_code)
            if student:
                subject = subject_by_student.get(student.id)
                # Update student metrics if columns exist
                if 'attendance' in row:
                    att_val = float(row['attendance'])
                    # Bug fix: was hardcoded to '2026-09-18'; now uses actual today's date
                    today = today_date.today().isoformat()
                    att_rec = Attendance(student_id=student.id, subject_id=subject.id, date=today, status="Present" if att_val >= 65 else "Absent", percentage=att_val)
                    db.session.add(att_rec)
                    
                if 'internal_marks' in row:
                    mks_val = float(row['internal_marks'])
                    # Bug fix: was hardcoded date '2026-09-18'
                    mks_rec = Mark(student_id=student.id, subject_id=subject.id, test_type="Batch Import", score=mks_val, date=today_date.today().isoformat())
                    db.session.add(mks_rec)
                    
                if 'study_hours' in row:
                    student.study_hours = float(row['study_hours'])
                    
                processed_count += 1
                queue_notification(
                    student.user_id,
                    'Academic records updated',
                    f'Your academic records and performance prediction were refreshed by {current_user.name}.',
                    'activity'
                )
                
                # Re-run ML Prediction for this updated student
                ml_data = {
                    'attendance': float(row.get('attendance', 75.0)),
                    'internal_marks': float(row.get('internal_marks', 65.0)),
                    'assignment_score': float(row.get('assignment_score', 70.0)),
                    'quiz_score': float(row.get('quiz_score', 65.0)),
                    'study_hours': float(row.get('study_hours', student.study_hours)),
                    'prev_gpa': float(student.prev_gpa),
                    'prev_sem_score': float(student.prev_gpa * 9.5),
                    'assignment_completion': float(row.get('assignment_score', 70.0)),
                    'participation': float(student.participation),
                    'backlogs': int(student.backlogs),
                    'recent_test_score': float(row.get('internal_marks', 65.0))
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
                updated_predictions += 1
                
        db.session.commit()
        return jsonify({
            'message': f'Dataset upload processed successfully! {processed_count} student records updated & {updated_predictions} ML predictions refreshed.',
            'rows_processed': processed_count
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'Error processing dataset: {str(e)}'}), 500
