import random
from app.models.models import FlashcardProgress, Flashcard, QuizAttempt, QuizQuestionAttempt
from app import db
from datetime import datetime
from app.services.ai_service import review_quiz_question_with_AI
from app.utils.validation_helpers import validate_quiz_difficulty

def normalize_answer(answer):
    return " ".join((answer or "").strip().lower().split())

def compute_score_percentage(correct_count, total_count):
    if total_count <= 0:
        return 0.0
    return round(correct_count / total_count * 100, 2)

# This function will most likely be moved to a repository folder in the future, but for now, it's here to keep things simple.
def get_quiz_attempt_for_user(quiz_attempt_id, user_id):
    quiz_attempt = QuizAttempt.query.filter_by(id=quiz_attempt_id, user_id=user_id).first()
    if not quiz_attempt:
        raise ValueError("Quiz attempt not found.")
    return quiz_attempt

# load questions for quiz, similar to study mode
def load_questions_for_quiz(user_id, note_id, topic_id=None, question_count=10, difficulty=None):
    validate_quiz_difficulty(difficulty, question_count)
    
    query = Flashcard.query.filter_by(user_id=user_id, note_id=note_id)
    if topic_id:
        query = query.filter_by(topic_id=topic_id)
    if difficulty:
        query = query.filter_by(difficulty=difficulty)

    cards = query.all()
    random.shuffle(cards)

    if question_count:
        cards = cards[:question_count]
    return cards

# create a quiz attempt and return the questions for the quiz.
def start_quiz(user_id, note_id, topic_id=None, question_count=10, difficulty=None):
    questions = load_questions_for_quiz(user_id=user_id, 
                                        note_id=note_id, 
                                        topic_id=topic_id,
                                        question_count=question_count,
                                        difficulty=difficulty)
    # This will most likely be changed to allow quizzes without a specific note or flashcards, but for now, let's keep it required.
    if not questions:
        raise ValueError("No flashcards available for the quiz with the given criteria.")
    
    quiz_attempt = QuizAttempt(user_id=user_id, topic_id=topic_id, note_id=note_id, question_order=[q.id for q in questions])
    db.session.add(quiz_attempt)
    db.session.commit()
    return quiz_attempt, questions

def get_current_quiz_question(user_id, quiz_attempt):
    attempt = get_quiz_attempt_for_user(quiz_attempt.id, quiz_attempt.user_id)
    order = attempt.question_order or []
    if not order:
        raise ValueError("Quiz attempt has no questions.")
    if attempt.question_index >= len(order):
        return None
    
    flashcard_id = order[attempt.question_index]
    flashcard = Flashcard.query.filter_by(id=flashcard_id, user_id=user_id).first()
    if not flashcard:
        raise ValueError("Flashcard not found for the current quiz question.")
    return flashcard

def submit_quiz_answer(user_id, quiz_attempt_id, flashcard_id, user_answer, time_taken=0):
    quiz_attempt = get_quiz_attempt_for_user(quiz_attempt_id, user_id)
    if quiz_attempt.status == 'completed':
        raise ValueError("Quiz attempt is already completed.")
    
    # This will most likely be changed to allow quizzes without a specific note or flashcards, but for now, let's keep it required.
    flashcard = Flashcard.query.filter_by(id=flashcard_id, user_id=user_id).first()
    if not flashcard:
        raise ValueError("Flashcard not found for the submitted answer.")
    
    is_correct = normalize_answer(user_answer) == normalize_answer(flashcard.answer)
    question_attempt = QuizQuestionAttempt.query.filter_by(quiz_attempt_id=quiz_attempt_id, flashcard_id=flashcard_id).first()

    if not question_attempt:
        question_attempt = QuizQuestionAttempt(quiz_attempt_id=quiz_attempt_id, 
                                               flashcard_id=flashcard_id,
                                               user_answer=user_answer or "",
                                               correct_answer=flashcard.answer,
                                               is_correct=is_correct,
                                               time_taken=float(time_taken or 0))
        db.session.add(question_attempt)  # Add the new question attempt record to the session
    else:
        question_attempt.user_answer = user_answer or ""
        question_attempt.correct_answer = flashcard.answer
        question_attempt.is_correct = is_correct
        question_attempt.time_taken = float(time_taken or 0)
    
    if quiz_attempt.question_order:
        try:
            position = quiz_attempt.question_order.index(flashcard_id)
        except ValueError:
            position = quiz_attempt.question_index
        quiz_attempt.question_index = max(quiz_attempt.question_index, position + 1)
    
    total_questions = len(quiz_attempt.question_order or [])
    correct_answers = QuizQuestionAttempt.query.filter_by(quiz_attempt_id=quiz_attempt_id, is_correct=True).count()
    quiz_attempt.score = compute_score_percentage(correct_answers, total_questions)

    if quiz_attempt.question_index >= total_questions:
        quiz_attempt.status = 'completed'
        quiz_attempt.finished_at = datetime.utcnow()
    db.session.commit()

    return {
        "quiz_attempt_id": quiz_attempt.id,
        "flashcard_id": flashcard_id,
        "is_correct": is_correct,
        "correct_answer": flashcard.answer,
        "score": quiz_attempt.score,
        "question_index": quiz_attempt.question_index,
        "status": quiz_attempt.status
    }

def finish_quiz(user_id, quiz_attempt_id):
    quiz_attempt = get_quiz_attempt_for_user(quiz_attempt_id, user_id)
    quiz_attempts = QuizQuestionAttempt.query.filter_by(quiz_attempt_id=quiz_attempt_id).all()
    
    total_questions = len(quiz_attempt.question_order or [])
    total_answered = len(quiz_attempts)
    total_correct = sum(1 for a in quiz_attempts if a.is_correct)
    quiz_attempt.score = compute_score_percentage(total_correct, total_questions)

    quiz_attempt.status = 'completed'
    quiz_attempt.finished_at = datetime.utcnow()
    db.session.commit()

    return {
        "quiz_attempt_id": quiz_attempt.id,
        "status": quiz_attempt.status, 
        "total_questions": total_questions,
        "total_answered": total_answered,
        "total_correct": total_correct,
        "score": quiz_attempt.score,
    }


# This function allows users to review their quiz questions and allow the AI agent to help them with questions they missed or found difficult. The feedback can be used to provide insights or suggestions for improvement.
def review_quiz_question(user_id, quiz_attempt_id, flashcard_id, feedback=None, ask_ai=False):
    get_quiz_attempt_for_user(quiz_attempt_id, user_id)  # Ensure the quiz attempt exists and belongs to the user
    
    question_attempt = QuizQuestionAttempt.query.filter_by(quiz_attempt_id=quiz_attempt_id, flashcard_id=flashcard_id).first()
    if not question_attempt:
        raise ValueError("Quiz question attempt not found for the given quiz attempt and flashcard.")
    
    flashcard = Flashcard.query.filter_by(id=flashcard_id, user_id=user_id).first()
    if not flashcard:
        raise ValueError("Flashcard not found for the given flashcard ID and user.")
    
    ai_feedback = None
    if ask_ai:
        ai_feedback = review_quiz_question_with_AI(user_id, quiz_attempt_id, flashcard_id, feedback)
    
    return {
        "quiz_attempt_id": quiz_attempt_id,
        "flashcard_id": flashcard_id,
        "question": flashcard.question,
        "user_answer": question_attempt.user_answer,
        "correct_answer": question_attempt.correct_answer,
        "is_correct": question_attempt.is_correct,
        "time_taken": question_attempt.time_taken,
        "ai_explanation": ai_feedback
    }

def get_quiz_review_summary(user_id, quiz_attempt_id, ask_ai=False, feedback=None):
    quiz_attempt = get_quiz_attempt_for_user(quiz_attempt_id, user_id)
    question_attempts = QuizQuestionAttempt.query.filter_by(quiz_attempt_id=quiz_attempt_id).all()
    
    total_questions = len(quiz_attempt.question_order or [])
    total_answered = len(question_attempts)
    total_correct = sum(1 for a in question_attempts if a.is_correct)
    score = compute_score_percentage(total_correct, total_questions)

    items = []
    for attempt in question_attempts:
        flashcard = Flashcard.query.filter_by(id=attempt.flashcard_id, user_id=user_id).first()
        if not flashcard:
            continue

        ai_feedback = None
        if ask_ai:
            ai_feedback = review_quiz_question_with_AI(user_id, quiz_attempt_id, attempt.flashcard_id, feedback=feedback)

        items.append({
            "flashcard_id": attempt.flashcard_id,
            "question": flashcard.question,
            "user_answer": attempt.user_answer,
            "correct_answer": attempt.correct_answer,
            "is_correct": attempt.is_correct,
            "time_taken": attempt.time_taken,
            "ai_explanation": ai_feedback
        })
    
    return {
        "quiz_attempt_id": quiz_attempt.id,
        "status": quiz_attempt.status, 
        "total_questions": total_questions,
        "total_answered": total_answered,
        "total_correct": total_correct,
        "score": score,
        'items': items,
    }
    



