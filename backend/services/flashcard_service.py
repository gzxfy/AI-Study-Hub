from sqlalchemy.exc import IntegrityError

from backend.models.models import (
    Flashcard,
    FlashcardProgress,
    Note,
    QuizAttempt,
    QuizQuestionAttempt,
    StudyEvent,
    Topic,
    db,
)
import backend.utils.validation_helpers as validation_helpers


UNSET = object()


class FlashcardNotFoundError(ValueError):
    """Raised when a flashcard is missing or not owned by the requesting user."""


class InvalidFlashcardTopicError(ValueError):
    """Raised when a flashcard topic is not owned or does not match its note."""


class FlashcardInUseError(ValueError):
    """Raised when study or quiz history still references a flashcard."""


def create_flashcard(user_id, topic_id, note_id, question, answer, difficulty=None):
    """Validate ownership and persist a flashcard associated with its note."""
    note = Note.query.filter_by(id=note_id, user_id=user_id).first()
    if note is None:
        raise ValueError("Note not found or unavailable.")

    if topic_id is not None:
        topic = Topic.query.filter_by(id=topic_id, user_id=user_id).first()
        if topic is None:
            raise InvalidFlashcardTopicError("Topic not found or unavailable.")

    if note.topic_id != topic_id:
        raise InvalidFlashcardTopicError(
            "topic_id must match the selected note's topic."
        )

    validation_helpers.validate_flashcard_data(question, answer, difficulty)
    flashcard = Flashcard(
        user_id=user_id,
        topic_id=topic_id,
        note_id=note_id,
        question=question,
        answer=answer,
        difficulty=difficulty,
    )
    try:
        db.session.add(flashcard)
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise
    return flashcard


def get_flashcard_by_id(flashcard_id, user_id=None):
    """Fetch a flashcard, optionally restricting the result to its owner."""
    query = Flashcard.query.filter_by(id=flashcard_id)
    if user_id is not None:
        query = query.filter_by(user_id=user_id)
    return query.first()


def get_all_flashcards(user_id):
    """Return all flashcards owned by the requested user."""
    return Flashcard.query.filter_by(user_id=user_id).all()


def edit_flashcard(
    flashcard_id,
    user_id,
    question=UNSET,
    answer=UNSET,
    difficulty=UNSET,
):
    """Validate and save the supplied fields on an owned flashcard."""
    flashcard = get_flashcard_by_id(flashcard_id, user_id)
    if flashcard is None:
        raise FlashcardNotFoundError("Flashcard not found.")

    try:
        if question is not UNSET:
            flashcard.question = question
        if answer is not UNSET:
            flashcard.answer = answer
        if difficulty is not UNSET:
            flashcard.difficulty = None if difficulty == "" else difficulty

        validation_helpers.validate_flashcard_data(
            flashcard.question,
            flashcard.answer,
            flashcard.difficulty,
        )
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise
    return flashcard


def delete_flashcard(flashcard_id, user_id):
    """Delete an unused flashcard, preserving its study and quiz history."""
    flashcard = (
        Flashcard.query
        .filter_by(id=flashcard_id, user_id=user_id)
        .with_for_update()
        .first()
    )
    if flashcard is None:
        raise FlashcardNotFoundError("Flashcard not found.")

    has_history = any((
        FlashcardProgress.query.filter_by(
            user_id=user_id,
            flashcard_id=flashcard_id,
        ).first(),
        StudyEvent.query.filter_by(
            user_id=user_id,
            flashcard_id=flashcard_id,
        ).first(),
        QuizQuestionAttempt.query.filter_by(flashcard_id=flashcard_id).first(),
    ))
    if not has_history:
        # Quiz attempts also retain selected IDs in a JSON array before answers exist.
        attempts = QuizAttempt.query.filter_by(user_id=user_id).with_for_update().all()
        has_history = any(
            flashcard_id in (attempt.question_order or [])
            for attempt in attempts
        )
    if has_history:
        raise FlashcardInUseError(
            "This flashcard has study or quiz history and cannot be deleted."
        )

    try:
        db.session.delete(flashcard)
        db.session.commit()
    except IntegrityError as error:
        db.session.rollback()
        raise FlashcardInUseError(
            "This flashcard is still referenced by study or quiz history."
        ) from error
    except Exception:
        db.session.rollback()
        raise
    return flashcard