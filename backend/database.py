from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timezone

db = SQLAlchemy()

class Department(db.Model):
    __tablename__ = 'departments'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    code = db.Column(db.String(20), nullable=False, unique=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), nullable=False, unique=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False) # admin, faculty, student
    department_id = db.Column(db.Integer, db.ForeignKey('departments.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

class Faculty(db.Model):
    __tablename__ = 'faculty'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, unique=True)
    department_id = db.Column(db.Integer, db.ForeignKey('departments.id'), nullable=False)
    employee_id = db.Column(db.String(50), nullable=False, unique=True)
    phone = db.Column(db.String(20))
    user = db.relationship('User', backref=db.backref('faculty_profile', uselist=False))
    department = db.relationship('Department')

class Student(db.Model):
    __tablename__ = 'students'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, unique=True)
    student_code = db.Column(db.String(50), nullable=False, unique=True)
    department_id = db.Column(db.Integer, db.ForeignKey('departments.id'), nullable=False)
    semester = db.Column(db.Integer, default=1)
    section = db.Column(db.String(10), default='A')
    gpa = db.Column(db.Float, default=0.0)
    prev_gpa = db.Column(db.Float, default=0.0)
    study_hours = db.Column(db.Float, default=0.0)
    backlogs = db.Column(db.Integer, default=0)
    participation = db.Column(db.Float, default=0.0)
    user = db.relationship('User', backref=db.backref('student_profile', uselist=False))
    department = db.relationship('Department')

class Subject(db.Model):
    __tablename__ = 'subjects'
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(20), nullable=False, unique=True)
    name = db.Column(db.String(100), nullable=False)
    department_id = db.Column(db.Integer, db.ForeignKey('departments.id'), nullable=False)
    credits = db.Column(db.Integer, default=3)
    semester = db.Column(db.Integer, default=1)
    department = db.relationship('Department')

class Attendance(db.Model):
    __tablename__ = 'attendance'
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    subject_id = db.Column(db.Integer, db.ForeignKey('subjects.id'), nullable=False)
    date = db.Column(db.String(20), nullable=False)
    status = db.Column(db.String(20), nullable=False) # Present, Absent, Excused
    percentage = db.Column(db.Float, default=0.0)
    student = db.relationship('Student')
    subject = db.relationship('Subject')

class Mark(db.Model):
    __tablename__ = 'marks'
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    subject_id = db.Column(db.Integer, db.ForeignKey('subjects.id'), nullable=False)
    test_type = db.Column(db.String(50), nullable=False)
    score = db.Column(db.Float, nullable=False)
    max_score = db.Column(db.Float, default=100.0)
    date = db.Column(db.String(20), nullable=False)
    student = db.relationship('Student')
    subject = db.relationship('Subject')

class Assignment(db.Model):
    __tablename__ = 'assignments'
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    subject_id = db.Column(db.Integer, db.ForeignKey('subjects.id'), nullable=False)
    title = db.Column(db.String(150), nullable=False)
    score = db.Column(db.Float, default=0.0)
    max_score = db.Column(db.Float, default=100.0)
    submitted = db.Column(db.Boolean, default=True)
    date = db.Column(db.String(20), nullable=False)
    student = db.relationship('Student')
    subject = db.relationship('Subject')

class Quiz(db.Model):
    __tablename__ = 'quizzes'
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    subject_id = db.Column(db.Integer, db.ForeignKey('subjects.id'), nullable=False)
    title = db.Column(db.String(150), nullable=False)
    score = db.Column(db.Float, default=0.0)
    max_score = db.Column(db.Float, default=100.0)
    date = db.Column(db.String(20), nullable=False)
    student = db.relationship('Student')
    subject = db.relationship('Subject')

class Prediction(db.Model):
    __tablename__ = 'predictions'
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    predicted_score = db.Column(db.Float, nullable=False)
    performance_category = db.Column(db.String(50), nullable=False)
    risk_level = db.Column(db.String(20), nullable=False)
    confidence = db.Column(db.Float, default=0.0)
    shap_explanation = db.Column(db.Text)
    model_used = db.Column(db.String(100), nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    student = db.relationship('Student')

class RiskAlert(db.Model):
    __tablename__ = 'risk_alerts'
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    warning_type = db.Column(db.String(100), nullable=False)
    risk_level = db.Column(db.String(20), nullable=False)
    message = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(20), default='Active') # Active, Resolved, Ignored
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    student = db.relationship('Student')

class Intervention(db.Model):
    __tablename__ = 'interventions'
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    faculty_id = db.Column(db.Integer, db.ForeignKey('faculty.id'), nullable=False)
    type = db.Column(db.String(100), nullable=False)
    notes = db.Column(db.Text)
    date = db.Column(db.String(20), nullable=False)
    student_response = db.Column(db.Text)
    next_review_date = db.Column(db.String(20))
    status = db.Column(db.String(20), default='In Progress')
    student = db.relationship('Student')
    faculty = db.relationship('Faculty')

class Notification(db.Model):
    __tablename__ = 'notifications'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    title = db.Column(db.String(150), nullable=False)
    message = db.Column(db.Text, nullable=False)
    type = db.Column(db.String(50), default='info')
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

class AuditLog(db.Model):
    __tablename__ = 'audit_logs'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    action = db.Column(db.String(150), nullable=False)
    details = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

class StudyMaterial(db.Model):
    __tablename__ = 'study_materials'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=True)
    original_file_name = db.Column(db.String(255), nullable=False)
    stored_file_name = db.Column(db.String(255), nullable=False)
    mime_type = db.Column(db.String(100), nullable=False)
    file_size = db.Column(db.Integer, nullable=False)
    extraction_status = db.Column(db.String(20), default='PROCESSING') # SUCCESS, FAILED, PROCESSING
    extraction_error = db.Column(db.Text, nullable=True)
    extracted_text = db.Column(db.Text, nullable=True)
    page_contents = db.Column(db.Text, nullable=True) # JSON list of {page, text}
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    user = db.relationship('User', backref=db.backref('study_materials', lazy=True))
    student = db.relationship('Student', backref=db.backref('study_materials', lazy=True))

class StudyChunk(db.Model):
    __tablename__ = 'study_chunks'
    id = db.Column(db.Integer, primary_key=True)
    study_material_id = db.Column(db.Integer, db.ForeignKey('study_materials.id'), nullable=False)
    page_number = db.Column(db.Integer, nullable=False)
    chunk_index = db.Column(db.Integer, nullable=False)
    text = db.Column(db.Text, nullable=False)
    
    study_material = db.relationship('StudyMaterial', backref=db.backref('chunks', cascade='all, delete-orphan', lazy=True))

class GeneratedQuiz(db.Model):
    __tablename__ = 'generated_quizzes'
    id = db.Column(db.Integer, primary_key=True)
    study_material_id = db.Column(db.Integer, db.ForeignKey('study_materials.id'), nullable=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=True)
    created_by_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    title = db.Column(db.String(200), nullable=False)
    difficulty = db.Column(db.String(50), default='Medium')
    questions = db.Column(db.Text, nullable=False) # JSON list of question objects
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    
    student = db.relationship('Student', backref=db.backref('generated_quizzes', lazy=True))
    created_by = db.relationship('User')
    study_material = db.relationship('StudyMaterial', backref=db.backref('generated_quizzes', lazy=True))

class QuizAttempt(db.Model):
    __tablename__ = 'quiz_attempts'
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    study_material_id = db.Column(db.Integer, db.ForeignKey('study_materials.id'), nullable=True)
    quiz_id = db.Column(db.Integer, db.ForeignKey('generated_quizzes.id'), nullable=True)
    score = db.Column(db.Float, nullable=False)
    total_questions = db.Column(db.Integer, nullable=False)
    percentage = db.Column(db.Float, nullable=False)
    topic_performance = db.Column(db.Text, nullable=True) # JSON
    weak_topics = db.Column(db.Text, nullable=True) # JSON
    submitted_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    
    student = db.relationship('Student', backref=db.backref('quiz_attempts', lazy=True))
    study_material = db.relationship('StudyMaterial', backref=db.backref('quiz_attempts', lazy=True))
    quiz = db.relationship('GeneratedQuiz', backref=db.backref('quiz_attempts', lazy=True))
