from datetime import timezone

from flask import Blueprint, current_app, jsonify, request, session

from backend import db
from backend.models.models import User
from backend.services import assistant_service


ai_assistant_bp = Blueprint("ai_assistant", __name__)


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
        current_app.logger.exception("Could not validate the assistant API session.")
        return None, api_error("internal_error", "Unable to access the assistant.", 500)

    return user_id, None


def message_payload():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return None, api_error("invalid_json", "Expected a JSON object.", 400)

    message = data.get("message")
    if not isinstance(message, str):
        return None, api_error("invalid_fields", "message must be a string.", 400)
    message = message.strip()
    if not message:
        return None, api_error("validation_error", "Message cannot be empty.", 400)
    if len(message) > assistant_service.QUESTION_LIMIT:
        return None, api_error(
            "validation_error",
            f"Message must be {assistant_service.QUESTION_LIMIT} characters or fewer.",
            400,
        )

    include_topic = data.get("include_topic", False)
    if not isinstance(include_topic, bool):
        return None, api_error("invalid_fields", "include_topic must be a boolean.", 400)

    request_id = data.get("request_id")
    if request_id is not None and (
        not isinstance(request_id, str) or not request_id or len(request_id) > 128
    ):
        return None, api_error(
            "invalid_request_id",
            "request_id must be a non-empty string of 128 characters or fewer.",
            400,
        )

    return {
        "message": message,
        "include_topic": include_topic,
        "request_id": request_id,
    }, None


def serialize_timestamp(value):
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    else:
        value = value.astimezone(timezone.utc)
    return value.isoformat().replace("+00:00", "Z")


def serialize_message(message):
    return {
        "id": message.id,
        "role": message.role,
        "content": message.content,
        "timestamp": serialize_timestamp(message.timestamp),
    }


def internal_error(message):
    db.session.rollback()
    current_app.logger.exception("Assistant API request failed.")
    return api_error("internal_error", message, 500)


@ai_assistant_bp.get("/api/notes/<int:note_id>/conversation")
def get_conversation(note_id):
    """Return the signed-in user's conversation for a note."""
    user_id, error_response = api_user_id()
    if error_response:
        return error_response

    try:
        messages = assistant_service.get_conversation_messages(note_id, user_id)
    except assistant_service.NoteNotFoundError:
        return api_error("not_found", "Note not found.", 404)
    except Exception:
        return internal_error("Unable to load conversation.")

    return api_json({"messages": [serialize_message(message) for message in messages]})


@ai_assistant_bp.post("/api/notes/<int:note_id>/messages")
def send_message(note_id):
    """Send a question and return the updated note conversation."""
    user_id, error_response = api_user_id()
    if error_response:
        return error_response

    data, error_response = message_payload()
    if error_response:
        return error_response

    try:
        messages = assistant_service.send_message(
            note_id=note_id,
            user_id=user_id,
            question=data["message"],
            include_topic=data["include_topic"],
            request_id=data["request_id"],
        )
    except assistant_service.NoteNotFoundError:
        return api_error("not_found", "Note not found.", 404)
    except ValueError as error:
        return api_error("validation_error", str(error), 400)
    except Exception:
        return internal_error("Unable to send message.")

    return api_json({"messages": [serialize_message(message) for message in messages]})