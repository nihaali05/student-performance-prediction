import os
import json
from datetime import datetime, timezone
from flask import Blueprint, request, jsonify, current_app
from werkzeug.utils import secure_filename
from sqlalchemy import and_, or_

from database import db, StudyMaterial, StudyChunk, GeneratedQuiz, QuizAttempt, Student, Subject, Quiz, Prediction, User
from auth_middleware import token_required
from services.notifications import queue_department_notifications
from services.document_extraction import process_uploaded_document
from services.retrieval import chunk_document_contents
from services.chat import answer_study_question
from services.ai_service import AIServiceError
from services.quiz import generate_study_quiz, evaluate_quiz_submission
from ml.predict import predict_student_performance

study_assistant_bp = Blueprint('study_assistant', __name__)


def _student_can_access_material(current_user, material):
    if material.user_id == current_user.id:
        return True
    owner = material.user
    return bool(
        owner
        and owner.role == 'faculty'
        and owner.department_id == current_user.department_id
    )


def _student_can_access_quiz(student, generated_quiz):
    if generated_quiz.student_id is not None:
        return generated_quiz.student_id == student.id
    material = generated_quiz.study_material
    if not material:
        return False
    owner = material.user
    return bool(
        owner
        and owner.role == 'faculty'
        and owner.department_id == student.department_id
    )


@study_assistant_bp.route('/upload', methods=['POST'])
@token_required()
def upload_study_material(current_user):
    if 'file' not in request.files:
        return jsonify({'message': 'No file part provided in request.'}), 400
        
    file = request.files['file']
    if not file or file.filename == '':
        return jsonify({'message': 'No file selected for upload.'}), 400
        
    original_filename = file.filename
    file_bytes = file.read()
    file_size = len(file_bytes)
    
    # Secure server storage name
    stored_filename = f"{current_user.id}_{int(datetime.now(timezone.utc).timestamp())}_{secure_filename(original_filename)}"
    os.makedirs(current_app.config['UPLOAD_FOLDER'], exist_ok=True)
    filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], stored_filename)
    
    with open(filepath, 'wb') as f:
        f.write(file_bytes)
        
    # Get associated student profile if student role
    student_profile = Student.query.filter_by(user_id=current_user.id).first()
    student_id = student_profile.id if student_profile else None
    
    # Process document extraction
    extraction_res = process_uploaded_document(file_bytes, original_filename, file.content_type)
    
    status = extraction_res.get('status', 'FAILED')
    error_msg = extraction_res.get('error')
    extracted_text = extraction_res.get('extracted_text')
    page_contents = extraction_res.get('page_contents')
    mime_type = extraction_res.get('mime_type', file.content_type or 'application/octet-stream')

    material = StudyMaterial(
        user_id=current_user.id,
        student_id=student_id,
        original_file_name=original_filename,
        stored_file_name=stored_filename,
        mime_type=mime_type,
        file_size=file_size,
        extraction_status=status,
        extraction_error=error_msg,
        extracted_text=extracted_text,
        page_contents=json.dumps(page_contents) if page_contents else None
    )
    db.session.add(material)
    db.session.commit()

    chunks_created = 0
    if status == 'SUCCESS' and page_contents:
        raw_chunks = chunk_document_contents(material.id, page_contents)
        for c in raw_chunks:
            chunk_obj = StudyChunk(
                study_material_id=material.id,
                page_number=c['page_number'],
                chunk_index=c['chunk_index'],
                text=c['text']
            )
            db.session.add(chunk_obj)
        db.session.commit()
        chunks_created = len(raw_chunks)

    if status == 'SUCCESS':
        if current_user.role == 'faculty' and current_user.faculty_profile:
            queue_department_notifications(
                current_user.faculty_profile.department_id,
                'student',
                f'New study material from {current_user.name}',
                f'{original_filename} is now available in Study Materials & Quiz.',
                'material'
            )
        elif current_user.role == 'student' and student_profile:
            queue_department_notifications(
                student_profile.department_id,
                'faculty',
                f'New study material from {current_user.name}',
                f'{original_filename} was uploaded by {current_user.name}.',
                'activity'
            )
        db.session.commit()

    # Return summary including Debug Preview for development verification
    preview_text = extracted_text[:800] if extracted_text else None
    
    if status == 'FAILED':
        return jsonify({
            'message': error_msg or 'Unable to read meaningful content from this study material.',
            'material': {
                'id': material.id,
                'originalFileName': original_filename,
                'extractionStatus': status,
                'extractionError': error_msg
            }
        }), 422

    return jsonify({
        'message': 'Study material uploaded and processed successfully.',
        'material': {
            'id': material.id,
            'originalFileName': original_filename,
            'mimeType': mime_type,
            'fileSize': file_size,
            'extractionStatus': status,
            'pageCount': len(page_contents) if page_contents else 1,
            'characterCount': len(extracted_text) if extracted_text else 0,
            'chunksCount': chunks_created,
            'extractedTextPreview': preview_text,
            'createdAt': material.created_at.isoformat()
        }
    }), 201


@study_assistant_bp.route('/materials', methods=['GET'])
@token_required()
def get_study_materials(current_user):
    query = StudyMaterial.query.join(User, StudyMaterial.user_id == User.id)
    if current_user.role == 'student':
        query = query.filter(or_(
            StudyMaterial.user_id == current_user.id,
            and_(
                User.role == 'faculty',
                User.department_id == current_user.department_id
            )
        ))
        
    materials = query.order_by(StudyMaterial.created_at.desc()).all()
    
    result = []
    for m in materials:
        page_list = json.loads(m.page_contents) if m.page_contents else []
        preview = m.extracted_text[:800] if m.extracted_text else None
        
        result.append({
            'id': m.id,
            'userId': m.user_id,
            'originalFileName': m.original_file_name,
            'mimeType': m.mime_type,
            'fileSize': m.file_size,
            'extractionStatus': m.extraction_status,
            'extractionError': m.extraction_error,
            'pageCount': len(page_list),
            'characterCount': len(m.extracted_text) if m.extracted_text else 0,
            'extractedTextPreview': preview,
            'createdAt': m.created_at.isoformat()
        })
        
    return jsonify({'materials': result, 'count': len(result)}), 200


@study_assistant_bp.route('/materials/<int:material_id>', methods=['GET'])
@token_required()
def get_study_material_detail(current_user, material_id):
    material = StudyMaterial.query.get_or_404(material_id)
    
    if current_user.role == 'student' and not _student_can_access_material(current_user, material):
        return jsonify({'message': 'Access denied to this study material.'}), 403

    page_list = json.loads(material.page_contents) if material.page_contents else []
    
    return jsonify({
        'material': {
            'id': material.id,
            'originalFileName': material.original_file_name,
            'mimeType': material.mime_type,
            'fileSize': material.file_size,
            'extractionStatus': material.extraction_status,
            'extractionError': material.extraction_error,
            'extractedText': material.extracted_text,
            'extractedTextPreview': material.extracted_text[:1000] if material.extracted_text else None,
            'pageContents': page_list,
            'pageCount': len(page_list),
            'characterCount': len(material.extracted_text) if material.extracted_text else 0,
            'createdAt': material.created_at.isoformat()
        }
    }), 200


@study_assistant_bp.route('/materials/<int:material_id>', methods=['DELETE'])
@token_required()
def delete_study_material(current_user, material_id):
    material = StudyMaterial.query.get_or_404(material_id)
    if current_user.role != 'admin' and material.user_id != current_user.id:
        return jsonify({'message': 'Access denied.'}), 403
        
    # Delete stored file on disk
    if material.stored_file_name:
        filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], material.stored_file_name)
        if os.path.exists(filepath):
            try:
                os.remove(filepath)
            except Exception:
                pass
                
    db.session.delete(material)
    db.session.commit()
    return jsonify({'message': 'Study material deleted successfully.'}), 200


@study_assistant_bp.route('/chat', methods=['POST'])
@token_required()
def chat_with_assistant(current_user):
    data = request.get_json() or {}
    if not isinstance(data, dict):
        return jsonify({'message': 'A JSON object is required.'}), 400
    question = data.get('question', '')
    if not isinstance(question, str):
        return jsonify({'message': 'Question text must be a string.'}), 400
    question = question.strip()
    material_id = data.get('study_material_id')
    
    if not question:
        return jsonify({'message': 'Question text is required.'}), 400
    if len(question) > 4000:
        return jsonify({'message': 'Question text must be 4,000 characters or fewer.'}), 400

    history = []
    raw_history = data.get('history', [])
    if isinstance(raw_history, list):
        for message in raw_history[-20:]:
            if not isinstance(message, dict):
                continue
            role = message.get('role')
            content = message.get('content')
            if role in ('user', 'assistant') and isinstance(content, str) and content.strip():
                history.append({'role': role, 'content': content.strip()[:2000]})

    chunks_query = StudyChunk.query.join(StudyMaterial)
    if material_id:
        material = db.session.get(StudyMaterial, material_id)
        if material:
            if current_user.role == 'student' and not _student_can_access_material(current_user, material):
                return jsonify({'message': 'Access denied to this study material.'}), 403
            chunks_query = chunks_query.filter(StudyMaterial.id == material_id)
        else:
            material_id = None
    elif current_user.role == 'student':
        chunks_query = chunks_query.join(User, StudyMaterial.user_id == User.id).filter(or_(
            StudyMaterial.user_id == current_user.id,
            and_(
                User.role == 'faculty',
                User.department_id == current_user.department_id
            )
        ))

    chunks = chunks_query.filter(StudyMaterial.extraction_status == 'SUCCESS').all()
    
    try:
        res = answer_study_question(question, chunks, history=history)
        return jsonify(res), 200
    except AIServiceError as exc:
        return jsonify({'message': str(exc)}), 503


@study_assistant_bp.route('/quiz/generate', methods=['POST'])
@token_required()
def generate_quiz(current_user):
    data = request.get_json() or {}
    student_profile = Student.query.filter_by(user_id=current_user.id).first()
    if current_user.role == 'student' and not student_profile:
        return jsonify({'message': 'A student profile is required to generate a quiz.'}), 403

    material_id = data.get('study_material_id')
    question_count = int(data.get('question_count', 5))
    difficulty = data.get('difficulty', 'Medium')
    
    chunks_query = StudyChunk.query.join(StudyMaterial)
    if material_id:
        material = db.session.get(StudyMaterial, material_id)
        if material:
            if current_user.role == 'student' and not _student_can_access_material(current_user, material):
                return jsonify({'message': 'Access denied to this study material.'}), 403
            chunks_query = chunks_query.filter(StudyMaterial.id == material_id)
        else:
            material_id = None
    elif current_user.role == 'student':
        chunks_query = chunks_query.join(User, StudyMaterial.user_id == User.id).filter(or_(
            StudyMaterial.user_id == current_user.id,
            and_(
                User.role == 'faculty',
                User.department_id == current_user.department_id
            )
        ))

    chunks = chunks_query.filter(StudyMaterial.extraction_status == 'SUCCESS').all()
    
    if not chunks:
        return jsonify({'message': 'No extracted study material available for quiz generation. Please upload a PDF or image first.'}), 400

    quiz_result = generate_study_quiz(chunks, question_count=question_count, difficulty=difficulty)
    generated_count = len(quiz_result.get('questions', []))
    if generated_count < question_count:
        return jsonify({
            'message': (
                f'Could generate only {generated_count} of the {question_count} requested exam-preparation questions '
                'from this material. Add more study content or choose a smaller question count.'
            )
        }), 422
    
    gen_quiz = GeneratedQuiz(
        study_material_id=material_id,
        student_id=student_profile.id if current_user.role == 'student' else None,
        created_by_user_id=current_user.id,
        title=quiz_result.get('title', 'Study Material Quiz'),
        difficulty=difficulty,
        questions=json.dumps(quiz_result.get('questions', []))
    )
    db.session.add(gen_quiz)
    db.session.commit()

    return jsonify({
        'quizId': gen_quiz.id,
        'title': gen_quiz.title,
        'difficulty': gen_quiz.difficulty,
        'questions': quiz_result.get('questions', []),
        'total': len(quiz_result.get('questions', []))
    }), 201


@study_assistant_bp.route('/quiz/submit', methods=['POST'])
@token_required()
def submit_quiz(current_user):
    data = request.get_json() or {}
    if not isinstance(data, dict):
        return jsonify({'message': 'A JSON object is required.'}), 400

    quiz_id = data.get('quiz_id')
    answers = data.get('answers', {})
    student_profile = Student.query.filter_by(user_id=current_user.id).first()
    if current_user.role != 'student' or not student_profile:
        return jsonify({'message': 'A student profile is required to submit a quiz.'}), 403
    if not isinstance(answers, dict):
        return jsonify({'message': 'Quiz answers must be an object.'}), 400
    if quiz_id is None:
        return jsonify({'message': 'A generated quiz ID is required for submission.'}), 400
    try:
        quiz_id = int(quiz_id)
    except (TypeError, ValueError):
        return jsonify({'message': 'Invalid quiz ID.'}), 400

    gen_quiz = GeneratedQuiz.query.get_or_404(quiz_id)
    if not _student_can_access_quiz(student_profile, gen_quiz):
        return jsonify({'message': 'Access denied to this quiz.'}), 403
    try:
        questions = json.loads(gen_quiz.questions)
    except (TypeError, json.JSONDecodeError):
        return jsonify({'message': 'Stored quiz content is invalid.'}), 500
    if not isinstance(questions, list) or not questions:
        return jsonify({'message': 'Stored quiz has no questions to evaluate.'}), 400

    student_id = student_profile.id
    material_id = gen_quiz.study_material_id

    evaluation = evaluate_quiz_submission(questions, answers)

    attempt = QuizAttempt(
        student_id=student_id,
        study_material_id=material_id,
        quiz_id=quiz_id,
        score=evaluation['score'],
        total_questions=evaluation['totalQuestions'],
        percentage=evaluation['percentage'],
        topic_performance=json.dumps(evaluation['topicPerformance']),
        weak_topics=json.dumps(evaluation['weakTopics'])
    )
    db.session.add(attempt)
    
    # Sync to the legacy Quiz table only when this student has a real subject.
    compatible_subject = Subject.query.filter_by(
        department_id=student_profile.department_id
    ).order_by(Subject.id).first()
    if compatible_subject:
        quiz_title = f"AI Quiz ({datetime.now().strftime('%Y-%m-%d')})"
        existing_quiz_record = Quiz(
            student_id=student_id,
            subject_id=compatible_subject.id,
            title=quiz_title,
            score=evaluation['percentage'],
            max_score=100.0,
            date=datetime.now().strftime('%Y-%m-%d')
        )
        db.session.add(existing_quiz_record)
    db.session.commit()

    # Recalculate ML prediction for student using actual data, not placeholders
    try:
        if student_profile:
            from database import Attendance, Mark
            quizzes = Quiz.query.filter_by(student_id=student_id).all()
            avg_qz = sum(q.score for q in quizzes) / len(quizzes) if quizzes else evaluation['percentage']
            
            # Bug fix: old code used hardcoded 80.0, 70.0, 75.0 - now uses real DB averages
            att_records = Attendance.query.filter_by(student_id=student_id).all()
            mark_records = Mark.query.filter_by(student_id=student_id).all()
            real_avg_att = sum(a.percentage for a in att_records) / len(att_records) if att_records else 75.0
            real_avg_mks = sum(m.score for m in mark_records) / len(mark_records) if mark_records else 65.0
            
            ml_data = {
                'attendance': real_avg_att,
                'internal_marks': real_avg_mks,
                'assignment_score': 75.0,
                'quiz_score': float(avg_qz),
                'study_hours': float(student_profile.study_hours or 10.0),
                'prev_gpa': float(student_profile.prev_gpa or 7.0),
                'prev_sem_score': float((student_profile.prev_gpa or 7.0) * 9.5),
                'assignment_completion': 75.0,
                'participation': float(student_profile.participation or 70.0),
                'backlogs': int(student_profile.backlogs or 0),
                'recent_test_score': float(evaluation['percentage'])
            }
            pred_res = predict_student_performance(ml_data)
            pred_obj = Prediction(
                student_id=student_id,
                predicted_score=pred_res['predicted_score'],
                performance_category=pred_res['performance_category'],
                risk_level=pred_res['risk_level'],
                confidence=pred_res['confidence'],
                shap_explanation=json.dumps(pred_res['xai']),
                model_used=pred_res['model_used']
            )
            db.session.add(pred_obj)
            db.session.commit()
    except Exception as e:
        print(f"[Quiz Submit] Recalculating prediction notice: {e}")

    if current_user.role == 'student' and student_profile:
        queue_department_notifications(
            student_profile.department_id,
            'faculty',
            f'Quiz submitted by {current_user.name}',
            f'{current_user.name} completed a study quiz with a score of {evaluation["percentage"]}%.',
            'activity'
        )
        db.session.commit()

    return jsonify({
        'attemptId': attempt.id,
        'score': evaluation['score'],
        'totalQuestions': evaluation['totalQuestions'],
        'percentage': evaluation['percentage'],
        'wrongCount': evaluation['wrongCount'],
        'correctCount': evaluation['correctCount'],
        'topicPerformance': evaluation['topicPerformance'],
        'weakTopics': evaluation['weakTopics'],
        'details': evaluation['details']
    }), 200


@study_assistant_bp.route('/quiz/history', methods=['GET'])
@token_required()
def get_quiz_history(current_user):
    student_profile = Student.query.filter_by(user_id=current_user.id).first()
    if current_user.role != 'student' or not student_profile:
        return jsonify({'message': 'A student profile is required to view quiz history.'}), 403
    student_id = student_profile.id
    
    attempts = QuizAttempt.query.filter_by(student_id=student_id).order_by(QuizAttempt.submitted_at.desc()).all()
    
    history = []
    all_weak_topics = set()
    
    for a in attempts:
        w_topics = json.loads(a.weak_topics) if a.weak_topics else []
        for wt in w_topics:
            all_weak_topics.add(wt)
            
        history.append({
            'id': a.id,
            'score': a.score,
            'totalQuestions': a.total_questions,
            'percentage': a.percentage,
            'weakTopics': w_topics,
            'submittedAt': a.submitted_at.isoformat()
        })
        
    return jsonify({
        'history': history,
        'totalAttempts': len(history),
        'weakTopicsSummary': list(all_weak_topics)
    }), 200
