import random
from datetime import datetime

from sqlalchemy.exc import IntegrityError

from backend import db
from backend.models.models import Flashcard, FlashcardProgress, StudyEvent
from backend.services.study_event import log_study_event
from backend.utils.validation_helpers import validate_study_difficulty


class FlashcardNotFoundError(ValueError):
    """Raised when a requested flashcard is not available to the user."""


class IdempotencyConflictError(ValueError):
    """Raised when a request ID is reused for a different review."""


def _validate_positive_id(value, field_name):
    if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
        raise ValueError(f"{field_name} must be a positive integer.")


def _validate_study_filters(user_id, note_id, difficulty, card_count):
    _validate_positive_id(user_id, "user_id")
    _validate_positive_id(note_id, "note_id")
    if card_count is not None and (
        not isinstance(card_count, int)
        or isinstance(card_count, bool)
        or card_count <= 0
    ):
        raise ValueError("card_count must be a positive integer.")
    if difficulty is not None and not isinstance(difficulty, str):
        raise ValueError("difficulty must be a string.")
    validate_study_difficulty(difficulty or None, card_count)


def load_flashcards_for_study(user_id, note_id, difficulty=None, card_count=None):
    """Load a user's flashcards for one note using optional study filters."""
    _validate_study_filters(user_id, note_id, difficulty, card_count)

    query = Flashcard.query.filter_by(user_id=user_id, note_id=note_id)
    if difficulty:
        query = query.filter_by(difficulty=difficulty)

    cards = query.all()
    random.shuffle(cards)
    if card_count is not None:
        cards = cards[:card_count]
    return cards


def _priority_key(card, progress_by_card):
    progress = progress_by_card.get(card.id)
    if progress is None or progress.times_seen == 0:
        return 0.0, 0, card.id

    accuracy = progress.times_correct / progress.times_seen
    return accuracy, progress.times_seen, card.id


def start_study_mode(
    user_id, note_id, difficulty=None, card_count=None, priority=False
):
    """Choose a user's eligible cards, optionally ranking weaker cards first."""
    _validate_study_filters(user_id, note_id, difficulty, card_count)
    if priority is None:
        priority = False
    if not isinstance(priority, bool):
        raise ValueError("priority must be a boolean.")

    query = Flashcard.query.filter_by(user_id=user_id, note_id=note_id)
    if difficulty:
        query = query.filter_by(difficulty=difficulty)
    cards = query.all()

    if priority and cards:
        card_ids = [card.id for card in cards]
        progress_rows = FlashcardProgress.query.filter(
            FlashcardProgress.user_id == user_id,
            FlashcardProgress.flashcard_id.in_(card_ids),
        ).all()
        progress_by_card = {
            progress.flashcard_id: progress for progress in progress_rows
        }
        # Rank the full eligible set before limiting so priority is meaningful.
        cards.sort(key=lambda card: _priority_key(card, progress_by_card))
    else:
        random.shuffle(cards)

    if card_count is not None:
        cards = cards[:card_count]
    return cards


def _existing_review_progress(user_id, flashcard_id, marked_correctly, request_id):
    event = StudyEvent.query.filter_by(
        user_id=user_id,
        request_id=request_id,
    ).first()
    if event is None:
        return None
    if event.flashcard_id != flashcard_id or event.is_correct != marked_correctly:
        raise IdempotencyConflictError(
            "This request ID was already used for a different review."
        )

    progress = FlashcardProgress.query.filter_by(
        user_id=user_id,
        flashcard_id=flashcard_id,
    ).first()
    if progress is None:
        raise RuntimeError("A saved review is missing its flashcard progress.")
    return progress


def review_flashcard(
    user_id, flashcard_id, marked_correctly, request_id=None
):
    """Persist one review event and update the user's card progress atomically."""
    _validate_positive_id(user_id, "user_id")
    _validate_positive_id(flashcard_id, "flashcard_id")
    if not isinstance(marked_correctly, bool):
        raise ValueError("marked_correctly must be a boolean.")
    if request_id is not None and (
        not isinstance(request_id, str)
        or not request_id.strip()
        or len(request_id) > 128
    ):
        raise ValueError("request_id must be a non-empty string up to 128 characters.")

    if request_id is not None:
        existing_progress = _existing_review_progress(
            user_id,
            flashcard_id,
            marked_correctly,
            request_id,
        )
        if existing_progress is not None:
            return existing_progress

    flashcard = Flashcard.query.filter_by(
        id=flashcard_id,
        user_id=user_id,
    ).with_for_update().first()
    if flashcard is None:
        raise FlashcardNotFoundError("Flashcard not found.")

    try:
        progress = FlashcardProgress.query.filter_by(
            user_id=user_id,
            flashcard_id=flashcard_id,
        ).first()
        if progress is None:
            progress = FlashcardProgress(
                user_id=user_id,
                flashcard_id=flashcard_id,
                times_seen=0,
                times_correct=0,
                streak=0,
                progress=0,
            )
            db.session.add(progress)

        log_study_event(
            user_id=user_id,
            flashcard_id=flashcard_id,
            is_correct=marked_correctly,
            source="study_mode",
            request_id=request_id,
        )

        progress.times_seen += 1
        if marked_correctly:
            progress.times_correct += 1
            progress.streak += 1
        else:
            progress.streak = 0

        progress.progress = progress.times_correct / progress.times_seen
        progress.last_seen = datetime.utcnow()
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        if request_id is not None:
            existing_progress = _existing_review_progress(
                user_id,
                flashcard_id,
                marked_correctly,
                request_id,
            )
            if existing_progress is not None:
                return existing_progress
        raise
    except Exception:
        db.session.rollback()
        raise

    return progress


def end_study_mode(user_id, reviewed_results):
    """Summarize a validated list of confirmed results for the session."""
    _validate_positive_id(user_id, "user_id")
    if not isinstance(reviewed_results, list):
        raise ValueError("reviewed_results must be a list.")

    correct_count = 0
    for result in reviewed_results:
        if not isinstance(result, dict):
            raise ValueError("Each reviewed result must be an object.")
        _validate_positive_id(result.get("flashcard_id"), "flashcard_id")
        if not isinstance(result.get("correct"), bool):
            raise ValueError("Each reviewed result must include a boolean correct value.")
        correct_count += result["correct"]

    reviewed_count = len(reviewed_results)
    accuracy = (
        round((correct_count / reviewed_count) * 100, 2)
        if reviewed_count
        else 0
    )
    return {
        "user_id": user_id,
        "reviewed_count": reviewed_count,
        "correct_count": correct_count,
        "accuracy": accuracy,
    }
