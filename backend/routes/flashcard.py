from datetime import timezone

from flask import jsonify, request, session, Blueprint, current_app
import backend.services.flashcard_service as flashcard_service
from backend import db
from backend.models import User

flashcard_bp = Blueprint('flashcard', __name__)

# Helper functions 
def internal_error(message):
    db.session.rollback()
    current_app.logger.exception("Flashcards API request failed.")
    return api_error("internal_error", message, 500)

def api_json(data, status=200):
    response = jsonify(data)
    response.headers["Cache-Control"] = "no-store"
    return response, status

def api_error(code, message, status):
    return api_json({"error": {"code": code, "message": message}}, status)

def api_user_id():
    user_id = session.get("user_id")
    if not isinstance(user_id, int) or isinstance(user_id, bool):
        session.clear()
        return None, api_error("unauthenticated", "Not authenticated.", 401)

    try:
        if db.session.get(User, user_id) is None:
            session.clear()
            return None, api_error("unauthenticated", "Not authenticated.", 401)
    except Exception:
        db.session.rollback()
        current_app.logger.exception("Could not validate the notes API session.")
        return None, api_error("internal_error", "Unable to access notes.", 500)

    return user_id, None

def json_payload(require_note_id=False):
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return None, api_error("invalid_json", "Expected a JSON object.", 400)

    if (
        not isinstance(data.get("question"), str)
        or not isinstance(data.get("answer"), str)
    ): 
        return None, api_error(
            "invalid_fields", 
            "Question and answer must be strings.", 
            400
        )

    if require_note_id and "note_id" not in data:
        return None, api_error(
            "invalid_note",
            "note_id must be a positive integer.",
            400,
        )
    note_id = data.get("note_id")
    if "note_id" in data and (
        not isinstance(note_id, int)
        or isinstance(note_id, bool)
        or note_id <= 0
    ):
        return None, api_error(
            "invalid_note",
            "note_id must be a positive integer.",
            400,
        )

    topic_id = data.get("topic_id")
    if topic_id is not None and (
        not isinstance(topic_id, int)
        or isinstance(topic_id, bool)
        or topic_id <= 0
    ):
        return None, api_error(
            "invalid_topic",
            "topic_id must be a positive integer or null.",
            400,
        )

    difficulty = data.get("difficulty")
    if difficulty is not None and not isinstance(difficulty, str):
        return None, api_error(
            "invalid_fields",
            "difficulty must be a string or null.",
            400,
        )

    return data, None

def serialize_timestamp(value):
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    else:
        value = value.astimezone(timezone.utc)
    return value.isoformat().replace("+00:00", "Z")


def serialize_topic(topic):
    if topic is None:
        return None
    return {"id": topic.id, "title": topic.title}


def serialize_flashcard(flashcard):
    serialized = {
        "id": flashcard.id,
        "note_id": flashcard.note_id,
        "topic_id": flashcard.topic_id,
        "question": flashcard.question,
        "answer": flashcard.answer,
        "difficulty": flashcard.difficulty,
        "created_at": serialize_timestamp(flashcard.created_at),
        "updated_at": serialize_timestamp(flashcard.updated_at),
    }
    
    return serialized

@flashcard_bp.post('/api/flashcards')
def api_create_flashcard():
    """Create a flashcard for the signed-in user and selected note."""
    user_id, error_report = api_user_id()
    if error_report:
        return error_report

    data, error_response = json_payload(require_note_id=True)
    if error_response:
        return error_response

    try: 
        flashcard = flashcard_service.create_flashcard(
            user_id=user_id,
            topic_id=data.get('topic_id'),
            note_id=data.get('note_id'),
            question=data.get('question'),
            answer=data.get('answer'),
            difficulty=data.get('difficulty')
        )
    except ValueError as error:
        return api_error("validation_error", str(error), 400)
    except Exception:
        return internal_error("Unable to create flashcard.")

    return api_json({"flashcard": serialize_flashcard(flashcard)}, 201)


@flashcard_bp.get('/api/flashcards/<int:flashcard_id>')
def api_view_flashcard(flashcard_id):
    """Display one flashcard after checking that it belongs to the user."""
    user_id, error_response = api_user_id()
    if error_response:
        return error_response

    try:
        flashcard = flashcard_service.get_flashcard_by_id(flashcard_id, user_id=user_id)
        if not flashcard or flashcard.user_id != user_id:
            return api_error("not_found", "Flashcard not found.", 404)
    except Exception:
        return internal_error("Unable to retrieve flashcard.")

    return api_json({"flashcard": serialize_flashcard(flashcard)})


@flashcard_bp.get('/api/flashcards')
def api_view_all_flashcards():
    """Display all flashcards owned by the signed-in user."""
    user_id , error_response = api_user_id()
    if error_response:
        return error_response

    try:
        flashcards = flashcard_service.get_all_flashcards(user_id)
        return api_json({"flashcards": [serialize_flashcard(f) for f in flashcards]})
    except Exception:
        return internal_error("Unable to retrieve flashcards.")


@flashcard_bp.patch('/api/flashcards/<int:flashcard_id>')
def api_update_flashcard(flashcard_id):
    """Update a user's flashcard."""
    user_id, error_response = api_user_id()
    if error_response:
        return error_response

    data, error_response = json_payload()
    if error_response:
        return error_response

    try:
        flashcard = flashcard_service.edit_flashcard(
            flashcard_id=flashcard_id,
            user_id=user_id,
            question=data.get('question', ''),
            answer=data.get('answer', ''),
            difficulty=data.get('difficulty', '')
        )
        if not flashcard or flashcard.user_id != user_id:
            return api_error("not_found", "Flashcard not found.", 404)
    except ValueError as ve:
        return api_error("validation_error", str(ve), 400)
    except Exception:
        return internal_error("Unable to update flashcard.")

    return api_json({"flashcard": serialize_flashcard(flashcard)})


@flashcard_bp.delete('/api/flashcards/<int:flashcard_id>')
def api_delete_flashcard(flashcard_id):
    """Delete an owned flashcard."""
    user_id, error_response = api_user_id()
    if error_response:
        return error_response

    try:
        flashcard_service.delete_flashcard(flashcard_id, user_id)
    except ValueError as ve:
        return api_error("validation_error", str(ve), 400)
    except Exception:
        return internal_error("Unable to delete flashcard.")

    response = current_app.response_class(status=204)
    response.headers["Cache-Control"] = "no-store"
    return response
