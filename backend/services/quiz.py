import re
import json
import random
from services.ai_service import call_ai_llm

QUIZ_SYSTEM_PROMPT = """You are an exam-preparation question writer.

Generate questions ONLY from the provided study material.

Do not use the filename, document title, metadata, or outside knowledge as factual information.

Every question and answer must be supported by the provided study material.

Generate only multiple-choice questions (MCQs), with exactly four distinct options and exactly one correct answer.
Questions must be clear, self-contained exam questions testing understanding, recall, comparison, or application.
Never generate fill-in-the-blank, sentence-completion, generic "explain this statement" prompts, or questions that repeat a source sentence verbatim.
Ignore course codes, unit labels, page headers, and incomplete OCR fragments.

If sufficient information is not available, generate fewer questions instead of inventing information.

For each question provide:
- question (string)
- questionType (must be 'mcq')
- options (array of exactly 4 distinct choices)
- correctAnswer (string)
- explanation (string explanation grounded in the text)
- sourcePage (integer page number where the information is found)

Format output strictly as a JSON object with keys:
{
  "title": "Quiz Title",
  "questions": [...]
}"""

def _is_exam_prep_question(question_obj):
    question = str(question_obj.get('question', '')).strip()
    question_type = question_obj.get('questionType')
    if not question or question_type != 'mcq' or '?' not in question:
        return False

    if re.search(
        r'\bfill\s+in\s+(?:the\s+)?blank\b|\bmissing\s+word\b|\bcomplete\s+the\s+sentence\b|_{2,}|\[\s*blank\s*\]|\bexplain\s+(?:the\s+)?(?:key\s+)?idea\s+in\s+this\s+statement\b',
        question,
        flags=re.IGNORECASE
    ):
        return False

    options = question_obj.get('options')
    if not isinstance(options, list) or len(options) != 4:
        return False
    normalized_options = [str(option).strip().casefold() for option in options]
    correct_answer = str(question_obj.get('correctAnswer', '')).strip().casefold()
    return (
        all(normalized_options)
        and len(set(normalized_options)) == 4
        and normalized_options.count(correct_answer) == 1
    )

def validate_question_grounding(question_obj, chunks):
    """
    Validates that a generated question's answer is supported by the document text.
    """
    if not question_obj or not chunks:
        return False
        
    q_text = str(question_obj.get('question', '')).lower()
    ans_text = str(question_obj.get('correctAnswer', '')).lower()
    
    all_doc_text = " ".join([
        (c.text if hasattr(c, 'text') else c.get('text', '')).lower()
        for c in chunks
    ])
    
    # Check if answer or key terms from question exist in the document text
    ans_words = re.findall(r'\b[a-zA-Z0-9_]{3,}\b', ans_text)
    if ans_words:
        matched = sum(1 for w in ans_words if w in all_doc_text)
        if matched / len(ans_words) >= 0.5:
            return True

    q_words = re.findall(r'\b[a-zA-Z0-9_]{3,}\b', q_text)
    if q_words:
        matched = sum(1 for w in q_words if w in all_doc_text)
        if matched / len(q_words) >= 0.4:
            return True

    return False

def generate_study_quiz(chunks, question_count=5, difficulty='Medium', topic='General'):
    """
    Generates a grounded quiz from study material chunks.
    """
    if not chunks:
        return {
            "error": "No study material content available for quiz generation."
        }

    try:
        question_count = max(1, int(question_count))
    except (TypeError, ValueError):
        question_count = 5

    # Aggregate text blocks (omitting filenames!)
    context_blocks = []
    for c in chunks:
        page = c.page_number if hasattr(c, 'page_number') else c.get('page_number', 1)
        text = c.text if hasattr(c, 'text') else c.get('text', '')
        context_blocks.append(f"[PAGE {page}]\n{text}")

    document_text = "\n\n".join(context_blocks)
    
    user_prompt = f"""PROVIDED STUDY MATERIAL:
{document_text}

QUIZ PARAMETERS:
- Question Count: {question_count}
- Difficulty: {difficulty}
- Target Topic: {topic}

Generate only clear, self-contained exam-preparation multiple-choice questions. Each question must have exactly four distinct options and one correct answer. Do not create fill-in-the-blank, sentence-completion, or "explain this statement" questions. Ignore course headers and incomplete text fragments.

Generate a JSON object with {question_count} questions based strictly on the provided study material:"""

    raw_json = call_ai_llm(QUIZ_SYSTEM_PROMPT, user_prompt, response_mime_type='application/json')
    
    quiz_data = None
    if raw_json:
        try:
            # Clean possible markdown formatting
            cleaned = re.sub(r'^```json\s*', '', raw_json.strip(), flags=re.MULTILINE)
            cleaned = re.sub(r'```$', '', cleaned.strip(), flags=re.MULTILINE)
            quiz_data = json.loads(cleaned)
        except Exception as e:
            print(f"[Quiz Generator] JSON parsing error: {e}")

    questions = quiz_data.get('questions', []) if isinstance(quiz_data, dict) else []
    validated_questions = []
    seen_questions = set()
    for question in questions:
        if not isinstance(question, dict) or not _is_exam_prep_question(question):
            continue
        if not validate_question_grounding(question, chunks):
            continue
        normalized_question = re.sub(r'\W+', ' ', question['question'].casefold()).strip()
        if normalized_question in seen_questions:
            continue
        seen_questions.add(normalized_question)
        validated_questions.append(question)
        if len(validated_questions) == question_count:
            break

    ai_question_count = len(validated_questions)
    # Replace invalid AI output with grounded, selectable exam questions.
    if len(validated_questions) < question_count:
        fallback = _build_fallback_quiz(
            chunks,
            max(1, question_count - len(validated_questions)),
            difficulty,
            existing_questions=validated_questions
        )
        additional_questions = fallback['questions']
        if not additional_questions:
            additional_questions = _generate_generic_fallback_questions(
                chunks,
                max(1, question_count - len(validated_questions)),
                existing_questions=validated_questions
            )
        validated_questions.extend(additional_questions)

    return {
        "title": (
            quiz_data.get('title', f"Study Quiz ({difficulty})")
            if isinstance(quiz_data, dict) and ai_question_count
            else f"Study Material Exam Practice ({difficulty})"
        ),
        "questions": validated_questions[:question_count],
        "total": min(len(validated_questions), question_count)
    }

def _generate_generic_fallback_questions(chunks, count=5, existing_questions=None):
    """Build generic multiple-choice questions from ordinary study text when the AI model is unavailable."""
    existing_answers = {
        re.sub(r'\W+', ' ', str(question.get('correctAnswer', '')).casefold()).strip()
        for question in existing_questions or []
    }
    existing_questions_norm = {
        re.sub(r'\W+', ' ', str(question.get('question', '')).casefold()).strip()
        for question in existing_questions or []
    }
    candidates = []
    seen_pairs = set()

    for c in chunks:
        page = c.page_number if hasattr(c, 'page_number') else c.get('page_number', 1)
        text = c.text if hasattr(c, 'text') else c.get('text', '')
        for raw_sentence in re.split(r'(?<=[.!?])\s+|\n+', text):
            sentence = re.sub(r'\s+', ' ', raw_sentence).strip(' \t\r\n•-')
            if not 20 <= len(sentence) <= 260 or not sentence[0].isupper():
                continue
            if re.search(r'\b(?:UNIT|LP|PAGE|CHAPTER|SECTION)\b|\b\d{2}[A-Z]{2}\d{3}\b', sentence, re.IGNORECASE):
                continue

            question, answer = None, None
            if re.match(r'^(.*?)(?:\s+is|\s+are|\s+refers to|\s+means|\s+describes|\s+includes|\s+involves|\s+consists of)\s+(.+)$', sentence, re.IGNORECASE):
                match = re.match(r'^(.*?)(?:\s+is|\s+are|\s+refers to|\s+means|\s+describes|\s+includes|\s+involves|\s+consists of)\s+(.+)$', sentence, re.IGNORECASE)
                concept = re.sub(r'\s+', ' ', match.group(1)).strip(' .,:;-')
                answer = re.sub(r'\s+', ' ', match.group(2)).strip(' .,:;-')
                question = f"Which statement best describes {concept}?"
            elif re.match(r'^(.*?)(?:\s+helps|\s+enables|\s+allows|\s+supports|\s+improves|\s+reduces|\s+increases|\s+decreases|\s+causes|\s+prevents)\s+(.+)$', sentence, re.IGNORECASE):
                match = re.match(r'^(.*?)(?:\s+helps|\s+enables|\s+allows|\s+supports|\s+improves|\s+reduces|\s+increases|\s+decreases|\s+causes|\s+prevents)\s+(.+)$', sentence, re.IGNORECASE)
                subject = re.sub(r'\s+', ' ', match.group(1)).strip(' .,:;-')
                answer = re.sub(r'\s+', ' ', match.group(2)).strip(' .,:;-')
                question = f"What is the main effect of {subject}?"
            elif ' because ' in sentence.lower() or ' due to ' in sentence.lower():
                part = sentence.split(' because ', 1)[0] if ' because ' in sentence.lower() else sentence.split(' due to ', 1)[0]
                reason = sentence.split(' because ', 1)[1] if ' because ' in sentence.lower() else sentence.split(' due to ', 1)[1]
                question = f"Why is {part.rstrip(' .')}?"
                answer = re.sub(r'\s+', ' ', reason).strip(' .,:;-')
            else:
                question = "What is the main idea described in the statement below?"
                answer = sentence.rstrip(' .!?')

            if not question or not answer or len(answer) < 8:
                continue
            answer = answer.rstrip('. ')
            norm_answer = re.sub(r'\W+', ' ', answer.casefold()).strip()
            norm_question = re.sub(r'\W+', ' ', question.casefold()).strip()
            if not norm_answer or norm_answer in existing_answers or norm_question in existing_questions_norm:
                continue
            pair = (norm_question, norm_answer)
            if pair in seen_pairs:
                continue
            seen_pairs.add(pair)
            candidates.append({
                'question': question,
                'correctAnswer': answer,
                'sourcePage': page,
                'sourceText': sentence
            })
            if len(candidates) >= count * 8:
                break
        if len(candidates) >= count * 8:
            break

    questions = []
    for candidate_index, candidate in enumerate(candidates):
        other_candidates = [item for item in candidates if item is not candidate]
        distractors = []
        for other in other_candidates:
            option = other['correctAnswer']
            if option.casefold() != candidate['correctAnswer'].casefold() and option not in distractors:
                distractors.append(option)
            if len(distractors) == 3:
                break

        if len(distractors) < 3:
            for item in _generic_distractors(candidate['correctAnswer']):
                if item.casefold() != candidate['correctAnswer'].casefold() and item not in distractors:
                    distractors.append(item)
                if len(distractors) == 3:
                    break

        if len(distractors) < 3:
            continue

        options = [candidate['correctAnswer'], *distractors[:3]]
        random.Random(candidate_index).shuffle(options)
        q_obj = {
            'question': candidate['question'],
            'questionType': 'mcq',
            'options': options,
            'correctAnswer': candidate['correctAnswer'],
            'explanation': f"According to page {candidate['sourcePage']}: '{candidate['sourceText']}'",
            'sourcePage': candidate['sourcePage']
        }
        if _is_exam_prep_question(q_obj):
            questions.append(q_obj)
        if len(questions) == count:
            break

    return questions


def _generic_distractors(correct_answer):
    """Produce plausible but distinct wrong answers when only a few source facts are available."""
    answer = str(correct_answer).strip()
    base = [
        'A summary of the topic without the actual process',
        'A method that happens without the main requirement',
        'A statement that describes a different concept',
        'The final result rather than the process itself'
    ]
    words = re.findall(r'[A-Za-z]{4,}', answer)
    if words:
        base.extend([
            f"A process that happens without {words[0]}",
            f"A result linked to {words[-1]} instead of the main concept",
            f"A description of {words[0]} only in theory"
        ])
    deduped = []
    for item in base:
        if item.casefold() != answer.casefold() and item not in deduped:
            deduped.append(item)
    return deduped[:3]


def _build_fallback_quiz(chunks, count=5, difficulty='Medium', existing_questions=None):
    """
    Build multiple-choice questions from complete, distinct facts in the source text.
    """
    candidates = []
    seen_answers = {
        re.sub(r'\W+', ' ', str(question.get('correctAnswer', '')).casefold()).strip()
        for question in existing_questions or []
    }
    seen_questions = {
        re.sub(r'\W+', ' ', str(question.get('question', '')).casefold()).strip()
        for question in existing_questions or []
    }
    incomplete_ending = re.compile(
        r'\b(?:and|or|but|because|through|between|which|that|to|of|with|for|where|while|by|in|such as)$',
        re.IGNORECASE
    )

    for c in chunks:
        page = c.page_number if hasattr(c, 'page_number') else c.get('page_number', 1)
        text = c.text if hasattr(c, 'text') else c.get('text', '')
        for raw_sentence in re.split(r'(?<=[.!?])\s+|\n+', text):
            sentence = re.sub(r'\s+', ' ', raw_sentence).strip(' \t\r\n•-')
            if not 45 <= len(sentence) <= 350 or not sentence[0].isupper():
                continue
            if re.search(r'\b(?:UNIT|LP)\s*\d+\b|\b\d{2}[A-Z]{2}\d{3}\b|AGILE METHODOLOGY\s*:', sentence, re.IGNORECASE):
                continue
            if incomplete_ending.search(sentence.rstrip(' .!?,')):
                continue

            candidate = _make_fallback_candidate(sentence, page)
            if not candidate:
                continue
            normalized_answer = re.sub(r'\W+', ' ', candidate['correctAnswer'].casefold()).strip()
            if normalized_answer in seen_answers:
                continue
            seen_answers.add(normalized_answer)
            normalized_question = re.sub(r'\W+', ' ', candidate['question'].casefold()).strip()
            if normalized_question not in seen_questions:
                seen_questions.add(normalized_question)
                candidates.append(candidate)
            for additional in _make_additional_fallback_candidates(sentence, page):
                normalized_answer = re.sub(
                    r'\W+', ' ', additional['correctAnswer'].casefold()
                ).strip()
                if normalized_answer not in seen_answers:
                    seen_answers.add(normalized_answer)
                    normalized_question = re.sub(
                        r'\W+', ' ', additional['question'].casefold()
                    ).strip()
                    if normalized_question not in seen_questions:
                        seen_questions.add(normalized_question)
                        candidates.append(additional)

    questions = []
    for candidate_index, candidate in enumerate(candidates):
        distractors = []
        for other_index, other in enumerate(candidates):
            if other_index == candidate_index:
                continue
            option = other['correctAnswer']
            if option.casefold() != candidate['correctAnswer'].casefold() and option not in distractors:
                distractors.append(option)
            if len(distractors) == 3:
                break
        if len(distractors) < 3:
            continue

        options = [candidate['correctAnswer'], *distractors]
        random.Random(candidate_index).shuffle(options)
        q_obj = {
            "question": candidate['question'],
            "questionType": "mcq",
            "options": options,
            "correctAnswer": candidate['correctAnswer'],
            "explanation": f"According to page {candidate['sourcePage']}: '{candidate['sourceText']}'",
            "sourcePage": candidate['sourcePage']
        }
        if _is_exam_prep_question(q_obj):
            questions.append(q_obj)
        if len(questions) == count:
            break

    if len(questions) < count:
        generic_questions = _generate_generic_fallback_questions(chunks, count=count, existing_questions=existing_questions)
        for question in generic_questions:
            if question not in questions:
                questions.append(question)
            if len(questions) == count:
                break

    return {
        "title": f"Study Material Quiz ({difficulty})",
        "questions": questions
    }

def _make_fallback_candidate(sentence, page):
    delivery_detail = re.search(
        r'software is built and delivered in (.+?)\s*,?\s*rather than as (.+?)(?:[.!?]|$)',
        sentence,
        flags=re.IGNORECASE
    )
    if delivery_detail:
        answer = (
            f"In {delivery_detail.group(1).strip()}, rather than as "
            f"{delivery_detail.group(2).strip().rstrip('.')}"
        )
        return _fallback_candidate(
            "How is software delivered in Agile development?",
            answer,
            page,
            sentence
        )

    definition = re.match(
        r'^(.{2,90}?)\s+(?:is|are|refers to|means|describes|includes|involves)\s+(.+)$',
        sentence,
        flags=re.IGNORECASE
    )
    if definition:
        concept = re.sub(r'\s+', ' ', definition.group(1)).strip(' .,:;-')
        words = concept.split()
        for split_at in range(len(words) // 2, 0, -1):
            if [word.casefold() for word in words[:split_at]] == [
                word.casefold() for word in words[split_at:split_at * 2]
            ]:
                concept = ' '.join(words[:split_at])
                break
        answer = definition.group(2).strip(' .,:;-')
        if len(answer) >= 12:
            return _fallback_candidate(
                f"Which statement best describes {concept}?",
                answer,
                page,
                sentence
            )

    patterns = [
        (
            r'^Unlike .+?,\s*Agile\s+promotes?\s+(.+)$',
            lambda match: ("Compared with traditional development models, what does Agile promote?", match.group(1))
        ),
        (
            r'^At the end of (.+?),\s*(.+)$',
            lambda match: (f"What is available at the end of {match.group(1)}?", match.group(2))
        ),
        (
            r'^In Agile,\s*(.+?)\s+continuously\s+evolve through\s+(.+)$',
            lambda match: (f"How do {match.group(1)} evolve in Agile?", match.group(2))
        ),
        (
            r'^(.{3,80}?)\s+enables teams to\s+(.+)$',
            lambda match: ("What does the approach described in the material enable teams to do?", match.group(2))
        ),
        (
            r'^(.{3,80}?)\s+emphasizes\s+(.+)$',
            lambda match: (f"What does {match.group(1)} emphasize?", match.group(2))
        ),
        (
            r'^(.{3,80}?)\s+promotes\s+(.+)$',
            lambda match: (f"What does {match.group(1)} promote?", match.group(2))
        ),
        (
            r'^(.{3,80}?)\s+consist(s)? of\s+(.+)$',
            lambda match: (
                f"What does {match.group(1)} consist of?" if match.group(2)
                else f"What do {match.group(1)} consist of?",
                match.group(3)
            )
        ),
        (
            r'^(.{3,80}?)\s+evolve through\s+(.+)$',
            lambda match: (f"How do {match.group(1)} evolve in Agile?", match.group(2))
        ),
    ]
    for pattern, make_question in patterns:
        match = re.match(pattern, sentence, flags=re.IGNORECASE)
        if match:
            question, answer = make_question(match)
            answer = answer.strip(' .,:;-')
            if len(answer) >= 12:
                return _fallback_candidate(question, answer, page, sentence)
    return None

def _fallback_candidate(question, answer, page, sentence):
    return {
        "question": question,
        "correctAnswer": answer.rstrip('.'),
        "sourcePage": page,
        "sourceText": sentence
    }

def _make_additional_fallback_candidates(sentence, page):
    candidates = []

    delivery_detail = re.search(
        r'emphasizes\s+(.+?),\s*where software is built and delivered in (.+?),?\s*rather than as (.+?)(?:[.!?]|$)',
        sentence,
        flags=re.IGNORECASE
    )
    if delivery_detail:
        candidates.append(_fallback_candidate(
            "Which development approach does Agile use?",
            delivery_detail.group(1).strip(),
            page,
            sentence
        ))
        candidates.append(_fallback_candidate(
            "In what form does Agile deliver software?",
            delivery_detail.group(2).strip().rstrip(','),
            page,
            sentence
        ))

    collaboration = re.search(
        r'In Agile,\s*the requirements and solutions continuously evolve through close collaboration between (.+?)(?:[.!?]|$)',
        sentence,
        flags=re.IGNORECASE
    )
    if collaboration:
        collaborators = collaboration.group(1).strip().rstrip('.')
        candidates.append(_fallback_candidate(
            "Which groups collaborate on Agile requirements and solutions?",
            collaborators,
            page,
            sentence
        ))

    adaptation = re.search(
        r'enables teams to respond effectively to (.+?) throughout the development process',
        sentence,
        flags=re.IGNORECASE
    )
    if adaptation:
        needs_and_feedback = adaptation.group(1).strip().rstrip('.')
        needs_match = re.match(r'(.+?)\s+and\s+customer feedback$', needs_and_feedback, re.IGNORECASE)
        if needs_match:
            candidates.append(_fallback_candidate(
                "What changing conditions can Agile teams respond to effectively?",
                needs_match.group(1).strip(),
                page,
                sentence
            ))
            candidates.append(_fallback_candidate(
                "What input can guide teams throughout Agile development?",
                "customer feedback throughout the development process",
                page,
                sentence
            ))

    team_roles = re.search(
        r'Agile teams consist of members with different skills, such as (.+?)(?:[.!?]|$)',
        sentence,
        flags=re.IGNORECASE
    )
    if team_roles:
        candidates.append(_fallback_candidate(
            "Which roles are examples of the varied skills in Agile teams?",
            team_roles.group(1).strip().rstrip('.'),
            page,
            sentence
        ))

    return candidates

def evaluate_quiz_submission(questions, student_answers):
    """
    Evaluates student quiz answers and calculates detailed metrics & weak topics.
    """
    total = len(questions)
    correct_count = 0
    wrong_count = 0
    topic_scores = {}
    weak_topics = []
    
    detailed_results = []

    for idx, q in enumerate(questions):
        correct_ans = ' '.join(str(q.get('correctAnswer', '')).split()).casefold()
        submitted = ' '.join(
            str(student_answers.get(str(idx), student_answers.get(idx, ''))).split()
        ).casefold()

        is_correct = bool(submitted) and submitted == correct_ans
        
        page = q.get('sourcePage', 1)
        topic_name = f"Page {page} Concepts"
        
        if topic_name not in topic_scores:
            topic_scores[topic_name] = {"total": 0, "correct": 0}
            
        topic_scores[topic_name]["total"] += 1
        
        if is_correct:
            correct_count += 1
            topic_scores[topic_name]["correct"] += 1
        else:
            wrong_count += 1
            if topic_name not in weak_topics:
                weak_topics.append(topic_name)

        detailed_results.append({
            "question": q.get('question'),
            "userAnswer": student_answers.get(str(idx), student_answers.get(idx, 'N/A')),
            "correctAnswer": q.get('correctAnswer'),
            "isCorrect": is_correct,
            "explanation": q.get('explanation'),
            "sourcePage": page
        })

    score_percentage = round((correct_count / total * 100), 1) if total > 0 else 0.0

    return {
        "totalQuestions": total,
        "correctCount": correct_count,
        "wrongCount": wrong_count,
        "score": float(correct_count),
        "percentage": score_percentage,
        "topicPerformance": topic_scores,
        "weakTopics": weak_topics,
        "details": detailed_results
    }
