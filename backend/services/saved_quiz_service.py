"""Manage attempts for quizzes whose questions are stored in quiz_questions."""

from datetime import datetime, timezone

from sqlalchemy import or_

from backend import db
from backend.models import Quiz, QuizAttempt, QuizQuestion, QuizQuestionAttempt, User
from backend.services.quiz_service import compute_score_percentage, normalize_answer


MAX_ATTEMPTS = 2


class QuizNotFoundError(ValueError):
    """The quiz or attempt is unavailable to this student."""


class QuizConflictError(ValueError):
    """The request conflicts with existing quiz progress."""


def list_saved_quizzes(user_id):
    """Return active shared quizzes and quizzes owned by this student."""
    quizzes = Quiz.query.filter(
        Quiz.is_active.is_(True), or_(Quiz.user_id.is_(None), Quiz.user_id == user_id)
    ).order_by(Quiz.title, Quiz.id)
    return [{"id": quiz.id, "title": quiz.title, "description": quiz.description} for quiz in quizzes]


def _lock_writes():
    # SQLite ignores row locks. Reserve its write transaction before reading state.
    if db.engine.dialect.name == "sqlite":
        db.session.execute(db.text("BEGIN IMMEDIATE"))


def _attempt_state(attempt):
    order = attempt.question_order
    question = None
    if attempt.status == "in_progress":
        current_question = QuizQuestion.query.filter_by(
            id=order[attempt.question_index], quiz_id=attempt.quiz_id
        ).first()
        if current_question is None:
            raise QuizConflictError("The current question is no longer available.")
        # The browser receives the prompt only. Grading happens on the server.
        question = {"id": current_question.id, "question": current_question.question_text}

    return {
        "quiz_id": attempt.quiz_id,
        "quiz_attempt_id": attempt.id,
        "status": attempt.status,
        "question_index": attempt.question_index,
        "total_questions": len(order),
        "question": question,
        "score": attempt.score if attempt.status == "completed" else None,
    }


def start_saved_quiz(user_id, quiz_id):
    """Resume an open attempt or create one within the student's attempt limit."""
    _lock_writes()
    # Serialize starts for this student so two requests cannot consume the same slot.
    if User.query.filter_by(id=user_id).with_for_update().first() is None:
        raise QuizNotFoundError("Student not found.")
    quiz = Quiz.query.filter(
        Quiz.id == quiz_id, Quiz.is_active.is_(True),
        or_(Quiz.user_id.is_(None), Quiz.user_id == user_id),
    ).first()
    if quiz is None:
        raise QuizNotFoundError("Quiz not found.")

    attempts = QuizAttempt.query.filter_by(user_id=user_id, quiz_id=quiz_id)
    attempt = attempts.filter_by(status="in_progress").order_by(QuizAttempt.id.desc()).first()
    if attempt is not None:
        state = _attempt_state(attempt)
        db.session.commit()
        return state, False
    if attempts.count() >= MAX_ATTEMPTS:
        raise QuizConflictError("You have used both attempts for this quiz.")

    questions = QuizQuestion.query.filter_by(quiz_id=quiz_id).order_by(QuizQuestion.id).all()
    if not questions:
        raise QuizConflictError("This quiz has no questions.")
    attempt = QuizAttempt(
        user_id=user_id, quiz_id=quiz_id, question_order=[question.id for question in questions]
    )
    db.session.add(attempt)
    db.session.flush()
    state = _attempt_state(attempt)
    db.session.commit()
    return state, True


def submit_saved_quiz_answer(user_id, attempt_id, question_id, user_answer):
    """Record the current answer and advance, or return progress for an exact retry."""
    _lock_writes()
    # Hold this attempt's row until the answer and progress commit together.
    attempt = QuizAttempt.query.filter_by(id=attempt_id, user_id=user_id).filter(
        QuizAttempt.quiz_id.is_not(None)
    ).with_for_update().first()
    if attempt is None:
        raise QuizNotFoundError("Quiz attempt not found.")

    previous = QuizQuestionAttempt.query.filter_by(
        quiz_attempt_id=attempt.id, quiz_question_id=question_id
    ).first()
    if previous is not None:
        if previous.user_answer != user_answer:
            raise QuizConflictError("This question already has a submitted answer.")
        state = _attempt_state(attempt)
        db.session.commit()
        return state

    if attempt.status != "in_progress" or attempt.question_order[attempt.question_index] != question_id:
        raise QuizConflictError("Answer the current question before continuing.")
    question = QuizQuestion.query.filter_by(id=question_id, quiz_id=attempt.quiz_id).first()
    if question is None:
        raise QuizConflictError("The current question is no longer available.")

    db.session.add(QuizQuestionAttempt(
        quiz_attempt_id=attempt.id,
        quiz_question_id=question.id,
        user_answer=user_answer,
        correct_answer=question.correct_answer,
        is_correct=normalize_answer(user_answer) == normalize_answer(question.correct_answer),
    ))
    attempt.question_index += 1
    if attempt.question_index == len(attempt.question_order):
        db.session.flush()
        correct_count = QuizQuestionAttempt.query.filter_by(
            quiz_attempt_id=attempt.id, is_correct=True
        ).count()
        attempt.score = compute_score_percentage(correct_count, len(attempt.question_order))
        attempt.status = "completed"
        attempt.finished_at = datetime.now(timezone.utc).replace(tzinfo=None)

    state = _attempt_state(attempt)
    db.session.commit()
    return state
