from flask import Blueprint, current_app, jsonify, request, session
from flask_wtf.csrf import CSRFError

from backend import db
from backend.models.models import User
from backend.services import study_mode_service


study_mode_bp = Blueprint("study_mode", __name__)


@study_mode_bp.errorhandler(CSRFError)
def csrf_error(_error):
    return api_error("csrf_failed", "CSRF token missing or invalid.", 400)


def api_json(data, status=200):
    response = jsonify(data)
    response.headers["Cache-Control"] = "no-store"
    return response, status


def api_error(code, message, status):
    return api_json({"error": {"code": code, "message": message}}, status)


def api_user_id():
    user_id = session.get("user_id")
    if not isinstance(user_id, int) or isinstance(user_id, bool) or user_id <= 0:
        session.clear()
        return None, api_error("unauthenticated", "Not authenticated.", 401)

    try:
        if db.session.get(User, user_id) is None:
            session.clear()
            return None, api_error("unauthenticated", "Not authenticated.", 401)
    except Exception:
        db.session.rollback()
        current_app.logger.exception("Could not validate the study API session.")
        return None, api_error("internal_error", "Unable to access study data.", 500)

    return user_id, None


def positive_integer(value, field_name):
    try:
        parsed_value = int(value)
    except (TypeError, ValueError):
        raise ValueError(f"{field_name} must be a positive integer.") from None
    if parsed_value <= 0 or str(parsed_value) != str(value).strip():
        raise ValueError(f"{field_name} must be a positive integer.")
    return parsed_value


def internal_error(message):
    db.session.rollback()
    current_app.logger.exception("Study API request failed.")
    return api_error("internal_error", message, 500)


@study_mode_bp.get("/study_mode/start")
def start_study_mode():
    """Return eligible study cards for one note and the requested filters."""
    user_id, error_response = api_user_id()
    if error_response:
        return error_response

    try:
        note_id = positive_integer(request.args.get("note_id"), "note_id")
        card_count_raw = request.args.get("card_count")
        card_count = (
            positive_integer(card_count_raw, "card_count")
            if card_count_raw is not None
            else None
        )
    except ValueError as error:
        return api_error("invalid_parameters", str(error), 400)

    difficulty = request.args.get("difficulty") or None
    priority_raw = request.args.get("priority")
    if priority_raw is None:
        priority = False
    elif priority_raw.lower() in ("true", "false"):
        priority = priority_raw.lower() == "true"
    else:
        return api_error(
            "invalid_priority",
            "priority must be 'true' or 'false'.",
            400,
        )

    try:
        cards = study_mode_service.start_study_mode(
            user_id=user_id,
            note_id=note_id,
            difficulty=difficulty,
            card_count=card_count,
            priority=priority,
        )
    except ValueError as error:
        return api_error("invalid_parameters", str(error), 400)
    except Exception:
        return internal_error("Unable to load study cards.")

    return api_json([
        {
            "id": card.id,
            "question": card.question,
            "answer": card.answer,
            "difficulty": card.difficulty,
        }
        for card in cards
    ])


@study_mode_bp.post("/study_mode/review")
def review_study_mode():
    """Record a confirmed answer and return the updated card progress."""
    user_id, error_response = api_user_id()
    if error_response:
        return error_response

    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return api_error("invalid_json", "Expected a JSON object.", 400)

    flashcard_id = payload.get("flashcard_id")
    marked_correctly = payload.get("marked_correctly")
    if (
        not isinstance(flashcard_id, int)
        or isinstance(flashcard_id, bool)
        or flashcard_id <= 0
        or not isinstance(marked_correctly, bool)
    ):
        return api_error(
            "invalid_fields",
            "flashcard_id must be a positive integer and marked_correctly must be a boolean.",
            400,
        )

    try:
        progress = study_mode_service.review_flashcard(
            user_id=user_id,
            flashcard_id=flashcard_id,
            marked_correctly=marked_correctly,
        )
    except study_mode_service.FlashcardNotFoundError:
        return api_error("not_found", "Flashcard not found.", 404)
    except ValueError as error:
        return api_error("validation_error", str(error), 400)
    except Exception:
        return internal_error("Unable to save flashcard review.")

    return api_json({
        "flashcard_id": progress.flashcard_id,
        "times_seen": progress.times_seen,
        "times_correct": progress.times_correct,
        "streak": progress.streak,
        "progress": progress.progress,
    })


@study_mode_bp.post("/study_mode/end")
def end_study_mode():
    """Summarize the confirmed review results submitted by the study client."""
    user_id, error_response = api_user_id()
    if error_response:
        return error_response

    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return api_error("invalid_json", "Expected a JSON object.", 400)

    try:
        summary = study_mode_service.end_study_mode(
            user_id=user_id,
            reviewed_results=payload.get("reviewed_results", []),
        )
    except ValueError as error:
        return api_error("invalid_fields", str(error), 400)
    except Exception:
        return internal_error("Unable to summarize the study session.")

    return api_json(summary)