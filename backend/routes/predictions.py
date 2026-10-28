import json
from flask import Blueprint, request, jsonify
from database import db, Student, Prediction, Attendance, Mark, Assignment, Quiz
from auth_middleware import token_required
from ml.predict import predict_student_performance

predictions_bp = Blueprint('predictions', __name__)

@predictions_bp.route('/run', methods=['POST'])
@token_required(allowed_roles=['admin', 'faculty'])
def run_batch_predictions(current_user):
    students_query = Student.query
    if current_user.role == 'faculty':
        faculty = current_user.faculty_profile
        if not faculty:
            return jsonify({'message': 'Faculty profile is not available.'}), 403
        students_query = students_query.filter_by(department_id=faculty.department_id)
    students = students_query.all()
    updated_count = 0
    
    for s in students:
        attendances = Attendance.query.filter_by(student_id=s.id).all()
        marks = Mark.query.filter_by(student_id=s.id).all()
        assignments = Assignment.query.filter_by(student_id=s.id).all()
        quizzes = Quiz.query.filter_by(student_id=s.id).all()
        
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
            'study_hours': float(s.study_hours),
            'prev_gpa': float(s.prev_gpa),
            'prev_sem_score': float(s.prev_gpa * 9.5),
            'assignment_completion': float(avg_asg),
            'participation': float(s.participation),
            'backlogs': int(s.backlogs),
            'recent_test_score': float(recent_mks)
        }
        
        try:
            pred_res = predict_student_performance(ml_data)
        except Exception as pred_err:
            # Bug fix: a single bad data row previously crashed the whole batch.
            # Now we skip faulty records and continue processing remaining students.
            print(f'[Batch Predict] Skipping student {s.id}: {pred_err}')
            continue

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
        updated_count += 1
        
    db.session.commit()
    return jsonify({'message': f'Successfully ran AI predictions for {updated_count} students.', 'count': updated_count}), 200

@predictions_bp.route('/what-if', methods=['POST'])
@token_required()
def what_if_simulator(current_user):
    data = request.get_json() or {}
    
    # Input sliders parameters
    input_data = {
        'attendance': float(data.get('attendance', 75.0)),
        'internal_marks': float(data.get('internal_marks', 65.0)),
        'assignment_score': float(data.get('assignment_score', 70.0)),
        'quiz_score': float(data.get('quiz_score', 65.0)),
        'study_hours': float(data.get('study_hours', 12.0)),
        'prev_gpa': float(data.get('prev_gpa', 7.0)),
        'prev_sem_score': float(data.get('prev_sem_score', 68.0)),
        'assignment_completion': float(data.get('assignment_completion', 75.0)),
        'participation': float(data.get('participation', 70.0)),
        'backlogs': int(data.get('backlogs', 0)),
        'recent_test_score': float(data.get('recent_test_score', 65.0))
    }
    
    res = predict_student_performance(input_data)
    
    return jsonify({
        'simulation': res,
        'disclaimer': 'Model-based scenario prediction. Results represent algorithmic projections based on trained feature weights, not a guaranteed outcome.'
    }), 200
