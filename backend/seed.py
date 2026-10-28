import os
import json
from sqlalchemy import inspect
from werkzeug.security import generate_password_hash
from database import (
    db, Department, User, Faculty, Student, Subject, Attendance, Mark,
    Assignment, Quiz, Prediction, RiskAlert, Intervention, Notification, AuditLog
)
from ml.predict import predict_student_performance


def _migrate_generated_quizzes():
    inspector = inspect(db.engine)
    if not inspector.has_table('generated_quizzes'):
        return

    columns = {column['name']: column for column in inspector.get_columns('generated_quizzes')}
    student_id = columns.get('student_id')
    needs_nullable_student = student_id is not None and not student_id['nullable']
    needs_creator = 'created_by_user_id' not in columns
    if not needs_nullable_student and not needs_creator:
        return

    if db.engine.dialect.name == 'sqlite':
        connection = db.engine.raw_connection()
        cursor = connection.cursor()
        foreign_keys_enabled = cursor.execute('PRAGMA foreign_keys').fetchone()[0]
        try:
            cursor.execute('PRAGMA foreign_keys=OFF')
            cursor.execute('BEGIN')
            existing_columns = {
                row[1] for row in cursor.execute('PRAGMA table_info(generated_quizzes)')
            }
            creator_column = (
                'created_by_user_id' if 'created_by_user_id' in existing_columns else 'NULL'
            )
            cursor.execute("""
                CREATE TABLE generated_quizzes_migration (
                    id INTEGER NOT NULL PRIMARY KEY,
                    study_material_id INTEGER,
                    student_id INTEGER,
                    created_by_user_id INTEGER,
                    title VARCHAR(200) NOT NULL,
                    difficulty VARCHAR(50),
                    questions TEXT NOT NULL,
                    created_at DATETIME,
                    FOREIGN KEY(study_material_id) REFERENCES study_materials (id),
                    FOREIGN KEY(student_id) REFERENCES students (id),
                    FOREIGN KEY(created_by_user_id) REFERENCES users (id)
                )
            """)
            cursor.execute(f"""
                INSERT INTO generated_quizzes_migration
                    (id, study_material_id, student_id, created_by_user_id,
                     title, difficulty, questions, created_at)
                SELECT id, study_material_id, student_id, {creator_column},
                       title, difficulty, questions, created_at
                FROM generated_quizzes
            """)
            cursor.execute('DROP TABLE generated_quizzes')
            cursor.execute(
                'ALTER TABLE generated_quizzes_migration RENAME TO generated_quizzes'
            )
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            cursor.execute(
                f'PRAGMA foreign_keys={"ON" if foreign_keys_enabled else "OFF"}'
            )
            cursor.close()
            connection.close()
    elif db.engine.dialect.name == 'mysql':
        with db.engine.begin() as connection:
            if needs_creator:
                connection.exec_driver_sql(
                    'ALTER TABLE generated_quizzes '
                    'ADD COLUMN created_by_user_id INTEGER NULL, '
                    'ADD CONSTRAINT fk_generated_quizzes_created_by_user '
                    'FOREIGN KEY (created_by_user_id) REFERENCES users(id)'
                )
            if needs_nullable_student:
                connection.exec_driver_sql(
                    'ALTER TABLE generated_quizzes MODIFY student_id INTEGER NULL'
                )


def seed_database(app):
    with app.app_context():
        db.create_all()
        _migrate_generated_quizzes()
        
        # Check if already seeded
        if User.query.first() is not None:
            print("Database already seeded.")
            return
            
        print("Seeding database with realistic initial data...")
        
        # 1. Departments
        cse = Department(name="Computer Science & Engineering", code="CSE")
        it = Department(name="Information Technology", code="IT")
        ds = Department(name="Data Science", code="DS")
        ee = Department(name="Electrical Engineering", code="EE")
        
        db.session.add_all([cse, it, ds, ee])
        db.session.commit()
        
        # 2. Users & Roles
        # Passwords hashed with pbkdf2:sha256 or werkzeug default
        admin_user = User(
            name="System Admin",
            email="admin@analytics.edu",
            password_hash=generate_password_hash("admin123"),
            role="admin",
            department_id=cse.id
        )
        
        fac1_user = User(
            name="Prof. Robert Smith",
            email="prof.smith@analytics.edu",
            password_hash=generate_password_hash("faculty123"),
            role="faculty",
            department_id=cse.id
        )
        
        fac2_user = User(
            name="Prof. Emily Johnson",
            email="prof.johnson@analytics.edu",
            password_hash=generate_password_hash("faculty123"),
            role="faculty",
            department_id=it.id
        )
        
        db.session.add_all([admin_user, fac1_user, fac2_user])
        db.session.commit()
        
        # 3. Faculty Profiles
        fac1 = Faculty(user_id=fac1_user.id, department_id=cse.id, employee_id="EMP-CSE-001", phone="+1 555-0192")
        fac2 = Faculty(user_id=fac2_user.id, department_id=it.id, employee_id="EMP-IT-002", phone="+1 555-0193")
        db.session.add_all([fac1, fac2])
        db.session.commit()
        
        # 4. Subjects
        sub1 = Subject(code="CS101", name="Data Structures & Algorithms", department_id=cse.id, credits=4, semester=3)
        sub2 = Subject(code="CS102", name="Database Management Systems", department_id=cse.id, credits=3, semester=3)
        sub3 = Subject(code="IT201", name="Web Development & APIs", department_id=it.id, credits=3, semester=3)
        sub4 = Subject(code="DS301", name="Machine Learning Fundamentals", department_id=ds.id, credits=4, semester=5)
        
        db.session.add_all([sub1, sub2, sub3, sub4])
        db.session.commit()
        
        # 5. Students & Profiles
        student_configs = [
            # Alex Jones - HIGH RISK / RED
            {
                "name": "Alex Jones", "email": "alex.jones@student.edu", "code": "STU-1001", "dept": cse.id, "sem": 3, "sec": "A",
                "gpa": 5.4, "prev_gpa": 5.8, "study_hours": 3.5, "backlogs": 2, "participation": 45.0,
                "attendance": 52.0, "internal_marks": 42.0, "assignment_score": 58.0, "quiz_score": 45.0,
                "assignment_completion": 50.0, "prev_sem_score": 54.0, "recent_test_score": 38.0
            },
            # Sarah Miller - HIGH PERFORMER / GREEN
            {
                "name": "Sarah Miller", "email": "sarah.miller@student.edu", "code": "STU-1002", "dept": cse.id, "sem": 3, "sec": "A",
                "gpa": 9.2, "prev_gpa": 9.1, "study_hours": 22.0, "backlogs": 0, "participation": 92.0,
                "attendance": 94.0, "internal_marks": 88.0, "assignment_score": 95.0, "quiz_score": 90.0,
                "assignment_completion": 98.0, "prev_sem_score": 90.0, "recent_test_score": 92.0
            },
            # David Brown - AVERAGE / YELLOW
            {
                "name": "David Brown", "email": "david.brown@student.edu", "code": "STU-1003", "dept": cse.id, "sem": 3, "sec": "B",
                "gpa": 6.8, "prev_gpa": 6.9, "study_hours": 8.0, "backlogs": 1, "participation": 65.0,
                "attendance": 74.0, "internal_marks": 62.0, "assignment_score": 70.0, "quiz_score": 60.0,
                "assignment_completion": 72.0, "prev_sem_score": 67.0, "recent_test_score": 58.0
            },
            # Emma Wilson - AT RISK / ORANGE
            {
                "name": "Emma Wilson", "email": "emma.wilson@student.edu", "code": "STU-1004", "dept": it.id, "sem": 3, "sec": "A",
                "gpa": 5.9, "prev_gpa": 6.2, "study_hours": 5.0, "backlogs": 1, "participation": 55.0,
                "attendance": 63.0, "internal_marks": 48.0, "assignment_score": 62.0, "quiz_score": 52.0,
                "assignment_completion": 58.0, "prev_sem_score": 60.0, "recent_test_score": 45.0
            },
            # Michael Chen - HIGH PERFORMER / GREEN
            {
                "name": "Michael Chen", "email": "michael.chen@student.edu", "code": "STU-1005", "dept": ds.id, "sem": 5, "sec": "A",
                "gpa": 8.8, "prev_gpa": 8.6, "study_hours": 18.0, "backlogs": 0, "participation": 88.0,
                "attendance": 91.0, "internal_marks": 85.0, "assignment_score": 90.0, "quiz_score": 86.0,
                "assignment_completion": 95.0, "prev_sem_score": 87.0, "recent_test_score": 89.0
            },
            # Jessica Taylor - HIGH RISK / RED
            {
                "name": "Jessica Taylor", "email": "jessica.taylor@student.edu", "code": "STU-1006", "dept": cse.id, "sem": 3, "sec": "B",
                "gpa": 4.8, "prev_gpa": 5.2, "study_hours": 2.0, "backlogs": 3, "participation": 38.0,
                "attendance": 48.0, "internal_marks": 36.0, "assignment_score": 45.0, "quiz_score": 38.0,
                "assignment_completion": 42.0, "prev_sem_score": 50.0, "recent_test_score": 32.0
            },
            # Daniel Martinez - AVERAGE / YELLOW
            {
                "name": "Daniel Martinez", "email": "daniel.martinez@student.edu", "code": "STU-1007", "dept": it.id, "sem": 3, "sec": "A",
                "gpa": 7.1, "prev_gpa": 7.0, "study_hours": 10.0, "backlogs": 0, "participation": 70.0,
                "attendance": 78.0, "internal_marks": 68.0, "assignment_score": 75.0, "quiz_score": 65.0,
                "assignment_completion": 80.0, "prev_sem_score": 72.0, "recent_test_score": 66.0
            },
            # Olivia Davis - AT RISK / ORANGE
            {
                "name": "Olivia Davis", "email": "olivia.davis@student.edu", "code": "STU-1008", "dept": ee.id, "sem": 3, "sec": "A",
                "gpa": 6.1, "prev_gpa": 6.5, "study_hours": 6.0, "backlogs": 2, "participation": 58.0,
                "attendance": 66.0, "internal_marks": 52.0, "assignment_score": 60.0, "quiz_score": 55.0,
                "assignment_completion": 64.0, "prev_sem_score": 63.0, "recent_test_score": 48.0
            }
        ]
        
        for sc in student_configs:
            u = User(
                name=sc['name'],
                email=sc['email'],
                password_hash=generate_password_hash("student123"),
                role="student",
                department_id=sc['dept']
            )
            db.session.add(u)
            db.session.commit()
            
            stu = Student(
                user_id=u.id,
                student_code=sc['code'],
                department_id=sc['dept'],
                semester=sc['sem'],
                section=sc['sec'],
                gpa=sc['gpa'],
                prev_gpa=sc['prev_gpa'],
                study_hours=sc['study_hours'],
                backlogs=sc['backlogs'],
                participation=sc['participation']
            )
            db.session.add(stu)
            db.session.commit()
            
            # Add attendance records
            att_rec = Attendance(
                student_id=stu.id,
                subject_id=sub1.id,
                date="2026-09-15",
                status="Present" if sc['attendance'] >= 65 else "Absent",
                percentage=sc['attendance']
            )
            db.session.add(att_rec)
            
            # Add marks records
            mks_rec1 = Mark(student_id=stu.id, subject_id=sub1.id, test_type="Midterm", score=sc['internal_marks'], date="2026-08-20")
            mks_rec2 = Mark(student_id=stu.id, subject_id=sub1.id, test_type="Unit Test 2", score=sc['recent_test_score'], date="2026-09-10")
            db.session.add_all([mks_rec1, mks_rec2])
            
            # Add assignment & quiz
            asg_rec = Assignment(student_id=stu.id, subject_id=sub1.id, title="Assignment 1 - Trees & Graphs", score=sc['assignment_score'], submitted=sc['assignment_completion'] > 50, date="2026-09-01")
            qz_rec = Quiz(student_id=stu.id, subject_id=sub1.id, title="Quiz 1 - Algorithm Complexity", score=sc['quiz_score'], date="2026-09-05")
            db.session.add_all([asg_rec, qz_rec])
            
            # Run ML Prediction for each student
            ml_input = {
                'attendance': sc['attendance'],
                'internal_marks': sc['internal_marks'],
                'assignment_score': sc['assignment_score'],
                'quiz_score': sc['quiz_score'],
                'study_hours': sc['study_hours'],
                'prev_gpa': sc['prev_gpa'],
                'prev_sem_score': sc['prev_sem_score'],
                'assignment_completion': sc['assignment_completion'],
                'participation': sc['participation'],
                'backlogs': sc['backlogs'],
                'recent_test_score': sc['recent_test_score']
            }
            
            pred_res = predict_student_performance(ml_input)
            
            pred_obj = Prediction(
                student_id=stu.id,
                predicted_score=pred_res['predicted_score'],
                performance_category=pred_res['performance_category'],
                risk_level=pred_res['risk_level'],
                confidence=pred_res['confidence'],
                shap_explanation=json.dumps(pred_res['xai']),
                model_used=pred_res['model_used']
            )
            db.session.add(pred_obj)
            
            # Generate Rule-based Risk Alerts if any
            for w in pred_res['rule_warnings']:
                alert_obj = RiskAlert(
                    student_id=stu.id,
                    warning_type=w['type'],
                    risk_level=w['risk_level'],
                    message=w['message'],
                    status='Active'
                )
                db.session.add(alert_obj)
                
            # Create user notification if high risk or at risk
            if pred_res['risk_level'] in ['RED', 'ORANGE']:
                notif = Notification(
                    user_id=u.id,
                    title=f"Early Warning: {pred_res['risk_level']} Risk Detected",
                    message=f"Your predicted score is {pred_res['predicted_score']}%. Please review recommendations and contact your advisor.",
                    type="warning"
                )
                db.session.add(notif)
                
        db.session.commit()
        
        # 6. Sample Faculty Interventions
        # Intervention for Alex Jones (Alex is student #1)
        stu_alex = Student.query.filter_by(student_code="STU-1001").first()
        if stu_alex:
            inv1 = Intervention(
                student_id=stu_alex.id,
                faculty_id=fac1.id,
                type="Academic Counseling & Mentoring",
                notes="Met with Alex regarding low attendance (52%) and midterm performance. Created a structured 3-week study plan.",
                date="2026-09-12",
                student_response="Student expressed enthusiasm and committed to attending all upcoming lectures.",
                next_review_date="2026-09-26",
                status="In Progress"
            )
            db.session.add(inv1)
            
        # Intervention for Jessica Taylor (Jessica is STU-1006)
        stu_jess = Student.query.filter_by(student_code="STU-1006").first()
        if stu_jess:
            inv2 = Intervention(
                student_id=stu_jess.id,
                faculty_id=fac1.id,
                type="Parent Meeting & Remedial Class",
                notes="Discussed severe backlog accumulation and low attendance. Parent informed.",
                date="2026-09-10",
                student_response="Agreed to attend daily remedial coaching from 4 PM - 5 PM.",
                next_review_date="2026-09-24",
                status="In Progress"
            )
            db.session.add(inv2)
            
        # 7. Audit Logs
        log1 = AuditLog(user_id=admin_user.id, action="SYSTEM_INIT", details="System initialized and seed data populated successfully.")
        log2 = AuditLog(user_id=fac1_user.id, action="MODEL_PREDICTION_BATCH", details="Executed ML prediction pipeline on batch 2026-09-18.")
        db.session.add_all([log1, log2])
        
        db.session.commit()
        print("Database seed completed successfully!")

if __name__ == '__main__':
    from flask import Flask
    from config import Config
    app = Flask(__name__)
    app.config.from_object(Config)
    db.init_app(app)
    seed_database(app)
