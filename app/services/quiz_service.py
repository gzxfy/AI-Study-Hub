import random
from app.models.models import FlashcardProgress, Flashcard, QuizAttempt, QuizQuestionAttempt
from app import db
from datetime import datetime
from app.utils.validation_helpers import validate_quiz_difficulty


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

def start_quiz(user_id, note_id, topic_id=None, question_count=10, difficulty=None):
    questions = load_questions_for_quiz(user_id=user_id, 
                                        note_id=note_id, 
                                        topic_id=topic_id,
                                        question_count=question_count,
                                        difficulty=difficulty)
    quiz_attempt = QuizAttempt(user_id=user_id, topic_id=topic_id, note_id=note_id, question_order=[q.id for q in questions])
    db.session.add(quiz_attempt)
    db.session.commit()
    return quiz_attempt, questions

# This function allows users to review their quiz questions and allow the AI agent to help them with questions they missed or found difficult. The feedback can be used to provide insights or suggestions for improvement.
def review_quiz_questions(user_id, quiz_attempt_id, flashcard_id, feedback=None):
    quiz_attempt = QuizAttempt.query.filter_by(quiz_attempt_id=quiz_attempt_id, user_id=user_id).first()
    if not quiz_attempt:
        raise ValueError("Quiz attempt not found.")
    
    question_attempt = QuizQuestionAttempt.query.filter_by(quiz_attempt_id=quiz_attempt_id, flashcard_id=flashcard_id).first()
    if not question_attempt:
        question_attempt = QuizQuestionAttempt(quiz_attempt_id=quiz_attempt_id, flashcard_id=flashcard_id)
        db.session.add(question_attempt)  # Add the new question attempt record to the session
    
    db.session.commit()

    if feedback is not None:
        pass
    pass


