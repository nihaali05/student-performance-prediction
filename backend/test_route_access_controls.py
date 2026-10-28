import io
import json
import unittest
from unittest.mock import patch

from flask import Flask

from auth_middleware import generate_token
from database import (
    db, Attendance, Department, Faculty, GeneratedQuiz, Intervention, Mark,
    Prediction, Quiz, QuizAttempt, RiskAlert, Student, Subject, User
)
from routes.attendance_marks import att_marks_bp
from routes.interventions import interventions_bp
from routes.predictions import predictions_bp
from routes.reports import reports_bp
from routes.study_assistant import study_assistant_bp
from routes.students import students_bp
from routes.upload import upload_bp
from routes.warnings import warnings_bp


class RouteAccessControlTests(unittest.TestCase):
    def setUp(self):
        self.app = Flask(__name__)
        self.app.config.update(
            TESTING=True,
            SECRET_KEY='route-tests-secret-key-32-bytes-minimum',
            JWT_SECRET_KEY='route-tests-jwt-secret-key-32-bytes-minimum',
            SQLALCHEMY_DATABASE_URI='sqlite:///:memory:',
            SQLALCHEMY_TRACK_MODIFICATIONS=False,
            UPLOAD_FOLDER='uploads/test-route-access'
        )
        db.init_app(self.app)
        self.app.register_blueprint(att_marks_bp, url_prefix='/api')
        self.app.register_blueprint(interventions_bp, url_prefix='/api/interventions')
        self.app.register_blueprint(predictions_bp, url_prefix='/api/predictions')
        self.app.register_blueprint(reports_bp, url_prefix='/api/reports')
        self.app.register_blueprint(study_assistant_bp, url_prefix='/api/study')
        self.app.register_blueprint(students_bp, url_prefix='/api/students')
        self.app.register_blueprint(upload_bp, url_prefix='/api/upload')
        self.app.register_blueprint(warnings_bp, url_prefix='/api/warnings')
        self.context = self.app.app_context()
        self.context.push()
        db.create_all()

        self.dept_a = Department(name='Department A', code='DA')
        self.dept_b = Department(name='Department B', code='DB')
        db.session.add_all([self.dept_a, self.dept_b])
        db.session.flush()

        self.admin = self._user('admin', self.dept_a.id)
        self.faculty_a_user = self._user('faculty', self.dept_a.id)
        self.faculty_b_user = self._user('faculty', self.dept_b.id)
        self.student_a_user = self._user('student', self.dept_a.id)
        self.student_b_user = self._user('student', self.dept_b.id)
        self.faculty_a = Faculty(
            user_id=self.faculty_a_user.id, department_id=self.dept_a.id,
            employee_id='FA'
        )
        self.faculty_b = Faculty(
            user_id=self.faculty_b_user.id, department_id=self.dept_b.id,
            employee_id='FB'
        )
        self.student_a = Student(
            user_id=self.student_a_user.id, student_code='SA',
            department_id=self.dept_a.id
        )
        self.student_b = Student(
            user_id=self.student_b_user.id, student_code='SB',
            department_id=self.dept_b.id
        )
        self.subject_a = Subject(
            code='A101', name='Subject A', department_id=self.dept_a.id
        )
        self.subject_b = Subject(
            code='B101', name='Subject B', department_id=self.dept_b.id
        )
        db.session.add_all([
            self.faculty_a, self.faculty_b, self.student_a, self.student_b,
            self.subject_a, self.subject_b
        ])
        db.session.flush()
        self.attendance_a = Attendance(
            student_id=self.student_a.id, subject_id=self.subject_a.id,
            date='2026-10-01', status='Present', percentage=90
        )
        self.attendance_b = Attendance(
            student_id=self.student_b.id, subject_id=self.subject_b.id,
            date='2026-10-01', status='Present', percentage=80
        )
        self.mark_a = Mark(
            student_id=self.student_a.id, subject_id=self.subject_a.id,
            test_type='Exam', score=80, max_score=100, date='2026-10-01'
        )
        self.mark_b = Mark(
            student_id=self.student_b.id, subject_id=self.subject_b.id,
            test_type='Exam', score=70, max_score=100, date='2026-10-01'
        )
        self.alert_a = RiskAlert(
            student_id=self.student_a.id, warning_type='risk',
            risk_level='RED', message='A alert'
        )
        self.alert_b = RiskAlert(
            student_id=self.student_b.id, warning_type='risk',
            risk_level='RED', message='B alert'
        )
        self.intervention_a = Intervention(
            student_id=self.student_a.id, faculty_id=self.faculty_a.id,
            type='check-in', date='2026-10-01'
        )
        self.intervention_b = Intervention(
            student_id=self.student_b.id, faculty_id=self.faculty_b.id,
            type='check-in', date='2026-10-01'
        )
        db.session.add_all([
            self.attendance_a, self.attendance_b, self.mark_a, self.mark_b,
            self.alert_a, self.alert_b, self.intervention_a, self.intervention_b
        ])
        db.session.commit()
        self.client = self.app.test_client()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        db.engine.dispose()
        self.context.pop()

    def _user(self, role, department_id):
        user = User(
            name=f'{role} {department_id}',
            email=f'{role}-{department_id}-{id(self)}@test.invalid',
            password_hash='unused',
            role=role,
            department_id=department_id
        )
        db.session.add(user)
        db.session.flush()
        return user

    def _headers(self, user):
        return {'Authorization': f'Bearer {generate_token(user)}'}

    def test_subject_attendance_and_marks_are_department_scoped(self):
        faculty_headers = self._headers(self.faculty_a_user)
        student_headers = self._headers(self.student_a_user)
        admin_headers = self._headers(self.admin)

        subjects = self.client.get('/api/subjects', headers=faculty_headers)
        self.assertEqual([s['code'] for s in subjects.json['subjects']], ['A101'])
        self.assertEqual(len(self.client.get(
            '/api/subjects', headers=admin_headers
        ).json['subjects']), 2)

        for endpoint, key in (('/api/attendance', 'attendance'), ('/api/marks', 'marks')):
            faculty_list = self.client.get(
                endpoint + f'?student_id={self.student_b.id}', headers=faculty_headers
            )
            self.assertEqual(faculty_list.json[key], [])
            own_student_list = self.client.get(
                endpoint + f'?student_id={self.student_b.id}', headers=student_headers
            )
            self.assertEqual(
                [record['student_id'] for record in own_student_list.json[key]],
                [self.student_a.id]
            )
            self.assertEqual(len(self.client.get(
                endpoint, headers=admin_headers
            ).json[key]), 2)

        cross_dept_attendance = self.client.post(
            '/api/attendance', headers=faculty_headers,
            json={
                'student_id': self.student_b.id, 'subject_id': self.subject_b.id,
                'status': 'Present', 'percentage': 50, 'date': '2026-10-02'
            }
        )
        self.assertEqual(cross_dept_attendance.status_code, 403)
        mismatched_subject = self.client.post(
            '/api/marks', headers=admin_headers,
            json={
                'student_id': self.student_a.id, 'subject_id': self.subject_b.id,
                'test_type': 'Exam', 'score': 50, 'max_score': 100,
                'date': '2026-10-02'
            }
        )
        self.assertEqual(mismatched_subject.status_code, 400)
        invalid_score = self.client.post(
            '/api/marks', headers=admin_headers,
            json={
                'student_id': self.student_a.id, 'subject_id': self.subject_a.id,
                'test_type': 'Exam', 'score': 101, 'max_score': 100,
                'date': '2026-10-02'
            }
        )
        self.assertEqual(invalid_score.status_code, 400)
        invalid_attendance = self.client.post(
            '/api/attendance', headers=admin_headers,
            json={
                'student_id': self.student_a.id, 'subject_id': self.subject_a.id,
                'status': 'Present', 'percentage': 101, 'date': '2026-10-02'
            }
        )
        self.assertEqual(invalid_attendance.status_code, 400)

        with patch('routes.attendance_marks.recalculate_student_prediction'):
            faculty_write = self.client.post(
                '/api/attendance', headers=faculty_headers,
                json={
                    'student_id': self.student_a.id, 'subject_id': self.subject_a.id,
                    'status': 'Present', 'percentage': 95, 'date': '2026-10-02'
                }
            )
            admin_write = self.client.post(
                '/api/marks', headers=admin_headers,
                json={
                    'student_id': self.student_b.id, 'subject_id': self.subject_b.id,
                    'test_type': 'Exam', 'score': 60, 'max_score': 100,
                    'date': '2026-10-02'
                }
            )
        self.assertEqual(faculty_write.status_code, 201)
        self.assertEqual(admin_write.status_code, 201)

    def test_warning_intervention_and_report_scopes(self):
        faculty_headers = self._headers(self.faculty_a_user)
        alerts = self.client.get('/api/warnings?status=All', headers=faculty_headers)
        self.assertEqual([item['student_id'] for item in alerts.json['alerts']], [self.student_a.id])
        denied = self.client.post(
            f'/api/warnings/{self.alert_b.id}/resolve', headers=faculty_headers
        )
        self.assertEqual(denied.status_code, 403)

        interventions = self.client.get(
            '/api/interventions', headers=faculty_headers
        ).json['interventions']
        self.assertEqual([item['student_id'] for item in interventions], [self.student_a.id])
        report = self.client.get(
            '/api/reports/download?type=student_performance',
            headers=faculty_headers
        )
        self.assertEqual(report.status_code, 200)
        self.assertIn('SA', report.get_data(as_text=True))
        self.assertNotIn('SB', report.get_data(as_text=True))

    def test_faculty_cannot_create_student_in_other_department(self):
        before_users = User.query.count()
        before_students = Student.query.count()
        response = self.client.post(
            '/api/students',
            headers=self._headers(self.faculty_a_user),
            json={
                'name': 'Out of department',
                'email': 'out-of-department@test.invalid',
                'student_code': 'OUT-1',
                'department_id': self.dept_b.id
            }
        )
        self.assertEqual(response.status_code, 403)
        self.assertEqual(User.query.count(), before_users)
        self.assertEqual(Student.query.count(), before_students)

    def test_admin_can_create_student_in_any_department(self):
        with patch('routes.students.predict_student_performance') as predict:
            predict.return_value = {
                'predicted_score': 75, 'performance_category': 'Average',
                'risk_level': 'GREEN', 'confidence': 90, 'xai': {},
                'model_used': 'test'
            }
            response = self.client.post(
                '/api/students',
                headers=self._headers(self.admin),
                json={
                    'name': 'New Department B Student',
                    'email': 'new-db-student@test.invalid',
                    'student_code': 'NEW-DB-1',
                    'department_id': self.dept_b.id
                }
            )
        self.assertEqual(response.status_code, 201, response.json)
        created = Student.query.filter_by(student_code='NEW-DB-1').one()
        self.assertEqual(created.department_id, self.dept_b.id)

    def test_admin_intervention_requires_matching_real_faculty(self):
        before_count = Intervention.query.count()
        no_faculty = self.client.post(
            '/api/interventions',
            headers=self._headers(self.admin),
            json={'student_id': self.student_a.id, 'type': 'check-in'}
        )
        self.assertEqual(no_faculty.status_code, 400)
        wrong_department = self.client.post(
            '/api/interventions',
            headers=self._headers(self.admin),
            json={
                'student_id': self.student_a.id,
                'faculty_id': self.faculty_b.id,
                'type': 'check-in'
            }
        )
        self.assertEqual(wrong_department.status_code, 400)
        missing_faculty = self.client.post(
            '/api/interventions',
            headers=self._headers(self.admin),
            json={
                'student_id': self.student_a.id, 'faculty_id': 999,
                'type': 'check-in'
            }
        )
        self.assertEqual(missing_faculty.status_code, 404)
        self.assertEqual(Intervention.query.count(), before_count)

        created = self.client.post(
            '/api/interventions',
            headers=self._headers(self.admin),
            json={
                'student_id': self.student_a.id,
                'faculty_id': self.faculty_a.id,
                'type': 'check-in'
            }
        )
        self.assertEqual(created.status_code, 201, created.json)
        intervention = Intervention.query.get(created.json['id'])
        self.assertEqual(intervention.faculty_id, self.faculty_a.id)

    def test_faculty_intervention_uses_own_faculty_profile(self):
        response = self.client.post(
            '/api/interventions',
            headers=self._headers(self.faculty_a_user),
            json={
                'student_id': self.student_a.id,
                'faculty_id': self.faculty_b.id,
                'type': 'check-in'
            }
        )
        self.assertEqual(response.status_code, 201, response.json)
        intervention = Intervention.query.get(response.json['id'])
        self.assertEqual(intervention.faculty_id, self.faculty_a.id)

    def test_batch_predictions_only_process_faculty_department(self):
        with patch('routes.predictions.predict_student_performance') as predict:
            predict.return_value = {
                'predicted_score': 75, 'performance_category': 'Average',
                'risk_level': 'GREEN', 'confidence': 90, 'xai': {},
                'model_used': 'test'
            }
            response = self.client.post(
                '/api/predictions/run', headers=self._headers(self.faculty_a_user)
            )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json['count'], 1)
        self.assertEqual(predict.call_count, 1)
        self.assertEqual(
            db.session.query(Prediction.student_id).filter(
                Prediction.student_id == self.student_b.id
            ).count(),
            0
        )

    def test_upload_rejects_out_of_department_before_writing(self):
        content = f'student_code,study_hours\n{self.student_b.student_code},10\n'
        with patch('builtins.open') as open_file:
            response = self.client.post(
                '/api/upload/csv',
                headers=self._headers(self.faculty_a_user),
                data={'file': (io.BytesIO(content.encode()), 'records.csv')},
                content_type='multipart/form-data'
            )
        self.assertEqual(response.status_code, 403)
        open_file.assert_not_called()
        self.assertEqual(
            db.session.query(Prediction).filter_by(student_id=self.student_b.id).count(),
            0
        )

    def test_upload_requires_student_code_column_before_writing(self):
        with patch('builtins.open') as open_file:
            response = self.client.post(
                '/api/upload/csv',
                headers=self._headers(self.admin),
                data={
                    'file': (io.BytesIO(b'attendance\n80\n'), 'records.csv')
                },
                content_type='multipart/form-data'
            )
        self.assertEqual(response.status_code, 400)
        self.assertIn('student_code', response.json['message'])
        open_file.assert_not_called()
        self.assertEqual(Attendance.query.count(), 2)

    def test_upload_rejects_missing_department_semester_subject_before_writing(self):
        self.student_a.semester = 2
        db.session.commit()
        content = 'student_code,attendance,internal_marks\nSA,85,75\n'
        with patch('builtins.open') as open_file:
            response = self.client.post(
                '/api/upload/csv',
                headers=self._headers(self.admin),
                data={'file': (io.BytesIO(content.encode()), 'records.csv')},
                content_type='multipart/form-data'
            )
        self.assertEqual(response.status_code, 400)
        self.assertIn('semester', response.json['message'])
        open_file.assert_not_called()
        self.assertEqual(Attendance.query.count(), 2)
        self.assertEqual(Mark.query.count(), 2)

    def test_upload_selects_subject_for_student_department_and_semester(self):
        self.student_a.semester = 2
        matching_subject = Subject(
            code='A201', name='Semester Two Subject',
            department_id=self.dept_a.id, semester=2
        )
        db.session.add(matching_subject)
        db.session.commit()
        content = 'student_code,attendance,internal_marks\nSA,85,75\n'
        with (
            patch('routes.upload.os.makedirs'),
            patch('builtins.open'),
            patch('routes.upload.predict_student_performance') as predict
        ):
            predict.return_value = {
                'predicted_score': 75, 'performance_category': 'Average',
                'risk_level': 'GREEN', 'confidence': 90, 'xai': {},
                'model_used': 'test'
            }
            response = self.client.post(
                '/api/upload/csv',
                headers=self._headers(self.admin),
                data={'file': (io.BytesIO(content.encode()), 'records.csv')},
                content_type='multipart/form-data'
            )
        self.assertEqual(response.status_code, 200, response.json)
        imported_attendance = Attendance.query.filter_by(
            student_id=self.student_a.id
        ).order_by(Attendance.id.desc()).first()
        imported_mark = Mark.query.filter_by(
            student_id=self.student_a.id
        ).order_by(Mark.id.desc()).first()
        self.assertEqual(imported_attendance.subject_id, matching_subject.id)
        self.assertEqual(imported_mark.subject_id, matching_subject.id)

    def test_quiz_attempt_is_saved_without_inventing_legacy_subject(self):
        no_subject_dept = Department(name='No Subject', code='NS')
        db.session.add(no_subject_dept)
        db.session.flush()
        student_user = self._user('student', no_subject_dept.id)
        no_subject_student = Student(
            user_id=student_user.id, student_code='NS1',
            department_id=no_subject_dept.id
        )
        db.session.add(no_subject_student)
        db.session.flush()
        generated_quiz = GeneratedQuiz(
            student_id=no_subject_student.id,
            created_by_user_id=student_user.id,
            title='Persisted quiz',
            questions=json.dumps([{
                'question': 'Question?', 'correctAnswer': 'answer', 'sourcePage': 1
            }])
        )
        db.session.add(generated_quiz)
        db.session.commit()

        with patch('routes.study_assistant.predict_student_performance') as predict:
            predict.return_value = {
                'predicted_score': 75, 'performance_category': 'Average',
                'risk_level': 'GREEN', 'confidence': 90, 'xai': {},
                'model_used': 'test'
            }
            response = self.client.post(
                '/api/study/quiz/submit',
                headers=self._headers(student_user),
                json={'quiz_id': generated_quiz.id, 'answers': {'0': 'answer'}}
            )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            QuizAttempt.query.filter_by(student_id=no_subject_student.id).count(), 1
        )
        self.assertEqual(Quiz.query.filter_by(student_id=no_subject_student.id).count(), 0)


if __name__ == '__main__':
    unittest.main()
