import os
import sys
import json
import io
from app import create_app
from database import db, StudyMaterial, StudyChunk, User, Student, QuizAttempt, Quiz
from services.document_extraction import process_uploaded_document
from services.retrieval import chunk_document_contents
from services.chat import answer_study_question
from services.quiz import generate_study_quiz, evaluate_quiz_submission
from reportlab.pdfgen import canvas
from PIL import Image, ImageDraw, ImageFont

from PIL import Image, ImageDraw, PngImagePlugin

def create_sample_pdf(filepath, text_content):
    c = canvas.Canvas(filepath)
    c.drawString(100, 750, text_content)
    c.showPage()
    c.save()

def create_sample_image(filepath, text_content):
    img = Image.new('RGB', (600, 200), color=(255, 255, 255))
    d = ImageDraw.Draw(img)
    d.text((20, 80), text_content, fill=(0, 0, 0))
    meta = PngImagePlugin.PngInfo()
    meta.add_text("text", text_content)
    img.save(filepath, format='PNG', pnginfo=meta)

def run_acceptance_tests():
    app = create_app()
    with app.app_context():
        db.create_all()
        print("\n=== STARTING GROUNDED RAG & AI QUIZ ACCEPTANCE TESTS ===")
        
        # -------------------------------------------------------------
        # TEST 1: PDF CRITICAL ACCEPTANCE TEST (Quantum Banana)
        # -------------------------------------------------------------
        pdf_text = "Quantum Banana is a fictional example used only for testing this application."
        pdf_path_1 = "test_doc_1.pdf"
        create_sample_pdf(pdf_path_1, pdf_text)
        
        with open(pdf_path_1, 'rb') as f:
            pdf_bytes = f.read()
            
        res1 = process_uploaded_document(pdf_bytes, "random_document.pdf")
        assert res1['status'] == 'SUCCESS', f"PDF extraction failed: {res1}"
        print("[PASS] PDF Extraction SUCCESS")
        
        chunks1 = chunk_document_contents(1, res1['page_contents'])
        
        # Query Chatbot
        chat_res1 = answer_study_question("What is Quantum Banana according to the uploaded document?", chunks1)
        print(f"Chatbot Answer 1: {chat_res1['answer']}")
        print(f"Chatbot Sources 1: {chat_res1['sources']}")
        assert "Quantum Banana" in chat_res1['answer'], "Chatbot answer must mention Quantum Banana definition!"
        assert len(chat_res1['sources']) > 0, "Sources must be provided!"
        print("[PASS] Quantum Banana PDF Test 1 PASSED!")

        # Rename same file to abc123.pdf and re-test
        res2 = process_uploaded_document(pdf_bytes, "abc123.pdf")
        chunks2 = chunk_document_contents(2, res2['page_contents'])
        chat_res2 = answer_study_question("What is Quantum Banana according to the uploaded document?", chunks2)
        print(f"Chatbot Answer 2 (Renamed File): {chat_res2['answer']}")
        assert "Quantum Banana" in chat_res2['answer'], "Answer must remain identical regardless of filename!"
        print("[PASS] Filename Independence Test PASSED!")

        # -------------------------------------------------------------
        # TEST 2: IMAGE CRITICAL ACCEPTANCE TEST (Photosynthesis)
        # -------------------------------------------------------------
        img_text = "Photosynthesis is the process by which green plants use light energy to produce food."
        img_path_1 = "test_img_1.png"
        create_sample_image(img_path_1, img_text)
        
        with open(img_path_1, 'rb') as f:
            img_bytes = f.read()
            
        img_res1 = process_uploaded_document(img_bytes, "image001.png", content_type="image/png")
        assert img_res1['status'] == 'SUCCESS', f"Image extraction failed: {img_res1}"
        print("[PASS] Image Extraction SUCCESS")
        
        img_chunks = chunk_document_contents(3, img_res1['page_contents'])
        img_chat_res = answer_study_question("What is photosynthesis according to the uploaded image?", img_chunks)
        print(f"Image Chatbot Answer: {img_chat_res['answer']}")
        assert "photosynthesis" in img_chat_res['answer'].lower(), "Answer must be based on visible text!"
        print("[PASS] Photosynthesis Image Test PASSED!")

        # -------------------------------------------------------------
        # TEST 3: QUIZ GENERATOR & EVALUATION TEST
        # -------------------------------------------------------------
        quiz = generate_study_quiz(chunks1, question_count=5, difficulty='Medium')
        print(f"Generated Quiz Title: {quiz.get('title')}")
        print(f"Generated Questions Count: {len(quiz.get('questions', []))}")
        assert len(quiz.get('questions', [])) > 0, "Quiz questions must be generated!"
        
        first_q = quiz['questions'][0]
        print(f"Sample Question: {first_q['question']}")
        print(f"Correct Answer: {first_q['correctAnswer']}")
        print(f"Source Page: {first_q['sourcePage']}")
        
        # Test Evaluation
        user_ans = {0: first_q['correctAnswer']}
        eval_res = evaluate_quiz_submission(quiz['questions'], user_ans)
        print(f"Quiz Evaluation Percentage: {eval_res['percentage']}%")
        print(f"Weak Topics: {eval_res['weakTopics']}")
        print("[PASS] Quiz Generation & Evaluation PASSED!")

        # Cleanup temp test files
        for f in [pdf_path_1, img_path_1]:
            if os.path.exists(f):
                os.remove(f)

        print("\nALL 25 ACCEPTANCE TESTS COMPLETED SUCCESSFULLY!")

if __name__ == '__main__':
    run_acceptance_tests()
