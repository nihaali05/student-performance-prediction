from flask import Blueprint, jsonify
from sqlalchemy import func
from database import db, Student, Faculty, Department, Prediction, RiskAlert, User
from auth_middleware import token_required

analytics_bp = Blueprint('analytics', __name__)

@analytics_bp.route('/admin', methods=['GET'])
@token_required(allowed_roles=['admin'])
def get_admin_analytics(current_user):
    total_students = Student.query.count()
    total_faculty = Faculty.query.count()
    total_departments = Department.query.count()
    
    # Bug fix: old code iterated ALL predictions and the dict kept the *last inserted* row
    # for each student_id, which might not be the most-recent by created_at.
    # Now we fetch only the latest prediction per student via a proper subquery.
    subq = (
        db.session.query(
            Prediction.student_id,
            func.max(Prediction.created_at).label('max_created_at')
        ).group_by(Prediction.student_id).subquery()
    )
    latest_pred_rows = (
        db.session.query(Prediction)
        .join(subq, (Prediction.student_id == subq.c.student_id) &
                    (Prediction.created_at == subq.c.max_created_at))
        .all()
    )
    latest_preds = {p.student_id: p for p in latest_pred_rows}
    predictions = latest_pred_rows  # for avg_performance calc
    
    if predictions:
        avg_performance = round(sum(p.predicted_score for p in predictions) / len(predictions), 1)
    else:
        avg_performance = 0.0
        
    green_count = sum(1 for p in latest_preds.values() if p.risk_level == 'GREEN')
    yellow_count = sum(1 for p in latest_preds.values() if p.risk_level == 'YELLOW')
    orange_count = sum(1 for p in latest_preds.values() if p.risk_level == 'ORANGE')
    red_count = sum(1 for p in latest_preds.values() if p.risk_level == 'RED')
    
    at_risk_count = orange_count + red_count
    high_risk_count = red_count
    improving_count = sum(1 for p in latest_preds.values() if p.performance_category == 'High Performer')
    declining_count = at_risk_count
    
    # Department breakdown
    dept_analytics = []
    departments = Department.query.all()
    for d in departments:
        dept_students = Student.query.filter_by(department_id=d.id).all()
        dept_student_ids = [s.id for s in dept_students]
        dept_preds = [latest_preds[sid] for sid in dept_student_ids if sid in latest_preds]
        
        dept_avg = round(sum(p.predicted_score for p in dept_preds) / len(dept_preds), 1) if dept_preds else 0.0
        dept_risk = sum(1 for p in dept_preds if p.risk_level in ['ORANGE', 'RED'])
        
        dept_analytics.append({
            'id': d.id,
            'name': d.name,
            'code': d.code,
            'student_count': len(dept_students),
            'avg_score': dept_avg,
            'at_risk_count': dept_risk
        })
        
    # Attendance vs Performance scatter / bin sample
    students = Student.query.all()
    scatter_data = []
    for s in students[:50]: # Sample 50
        pred = latest_preds.get(s.id)
        scatter_data.append({
            'name': s.user.name,
            'study_hours': s.study_hours,
            'gpa': s.gpa,
            'predicted_score': pred.predicted_score if pred else 70.0,
            'risk_level': pred.risk_level if pred else 'GREEN'
        })
        
    return jsonify({
        'total_students': total_students,
        'total_faculty': total_faculty,
        'total_departments': total_departments,
        'avg_performance': avg_performance,
        'at_risk_students': at_risk_count,
        'high_risk_students': high_risk_count,
        'improving_students': improving_count,
        'declining_students': declining_count,
        'risk_distribution': [
            {'name': 'Normal (Green)', 'value': green_count, 'color': '#10B981'},
            {'name': 'Needs Attention (Yellow)', 'value': yellow_count, 'color': '#F59E0B'},
            {'name': 'At Risk (Orange)', 'value': orange_count, 'color': '#F97316'},
            {'name': 'High Risk (Red)', 'value': red_count, 'color': '#EF4444'}
        ],
        'department_analytics': dept_analytics,
        'scatter_data': scatter_data
    }), 200
