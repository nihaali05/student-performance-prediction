import io
import csv
from flask import Blueprint, request, Response, jsonify
from database import Student, Prediction, Department, RiskAlert, Attendance, Mark
from auth_middleware import token_required

reports_bp = Blueprint('reports', __name__)

@reports_bp.route('/download', methods=['GET'])
@token_required(allowed_roles=['admin', 'faculty'])
def download_report(current_user):
    report_type = request.args.get('type', 'at_risk') # at_risk, student_performance, department, predictions
    file_format = request.args.get('format', 'csv') # csv or txt
    faculty = current_user.faculty_profile if current_user.role == 'faculty' else None
    if current_user.role == 'faculty' and not faculty:
        return jsonify({'message': 'Faculty profile is not available.'}), 403
    
    output = io.StringIO()
    writer = csv.writer(output)
    
    if report_type == 'at_risk':
        filename = "at_risk_students_report.csv"
        writer.writerow(["Student Code", "Student Name", "Department", "GPA", "Attendance %", "Predicted Score", "Risk Level"])
        
        preds_query = Prediction.query.join(Student).filter(
            Prediction.risk_level.in_(['ORANGE', 'RED'])
        )
        if faculty:
            preds_query = preds_query.filter(Student.department_id == faculty.department_id)
        preds = preds_query.all()
        for p in preds:
            s = p.student
            att_records = Attendance.query.filter_by(student_id=s.id).all()
            avg_att = sum(a.percentage for a in att_records) / len(att_records) if att_records else 0.0
            writer.writerow([s.student_code, s.user.name, s.department.name, s.gpa, round(avg_att, 1), p.predicted_score, p.risk_level])
            
    elif report_type == 'student_performance':
        filename = "student_performance_summary.csv"
        writer.writerow(["Student Code", "Name", "Department", "Semester", "GPA", "Study Hours", "Backlogs", "Predicted Score", "Category", "Risk Level"])
        
        students_query = Student.query
        if faculty:
            students_query = students_query.filter_by(department_id=faculty.department_id)
        students = students_query.all()
        for s in students:
            p = Prediction.query.filter_by(student_id=s.id).order_by(Prediction.created_at.desc()).first()
            writer.writerow([
                s.student_code, s.user.name, s.department.name, s.semester, s.gpa, s.study_hours, s.backlogs,
                p.predicted_score if p else 'N/A',
                p.performance_category if p else 'N/A',
                p.risk_level if p else 'N/A'
            ])
            
    elif report_type == 'department':
        filename = "department_analytics_report.csv"
        writer.writerow(["Department Code", "Department Name", "Total Students", "Average Predicted Score", "At-Risk Student Count"])
        
        depts_query = Department.query
        if faculty:
            depts_query = depts_query.filter_by(id=faculty.department_id)
        depts = depts_query.all()
        for d in depts:
            dept_students = Student.query.filter_by(department_id=d.id).all()
            s_ids = [s.id for s in dept_students]
            preds = Prediction.query.filter(Prediction.student_id.in_(s_ids)).all() if s_ids else []
            avg_sc = round(sum(p.predicted_score for p in preds) / len(preds), 1) if preds else 0.0
            at_risk = sum(1 for p in preds if p.risk_level in ['ORANGE', 'RED'])
            writer.writerow([d.code, d.name, len(dept_students), avg_sc, at_risk])
            
    else:
        return jsonify({'message': 'Invalid report type requested.'}), 400
        
    output.seek(0)
    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-disposition": f"attachment; filename={filename}"}
    )
