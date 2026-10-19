from datetime import timezone

from flask import Blueprint, current_app, jsonify, request, session

from backend import db
from backend.models.models import User
from backend.services import topic_service

topic_bp = Blueprint("topic", __name__)


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
        current_app.logger.exception("Could not validate the topics API session.")
        return None, api_error("internal_error", "Unable to access topics.", 500)

    return user_id, None


def topic_payload():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return None, api_error("invalid_json", "Expected a JSON object.", 400)

    fields = ("title", "description", "color")
    if any(not isinstance(data.get(field), str) for field in fields):
        return None, api_error(
            "invalid_fields",
            "Title, description, and color must be strings.",
            400,
        )
    return data, None


def serialize_timestamp(value):
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    else:
        value = value.astimezone(timezone.utc)
    return value.isoformat().replace("+00:00", "Z")


def serialize_topic(topic, note_count):
    return {
        "id": topic.id,
        "title": topic.title,
        "description": topic.description,
        "color": topic.color,
        "note_count": note_count,
        "created_at": serialize_timestamp(topic.created_at),
        "updated_at": serialize_timestamp(topic.updated_at),
    }


def serialize_note_summary(note):
    return {
        "id": note.id,
        "title": note.title,
        "excerpt": " ".join(note.content.split())[:160],
        "topic_id": note.topic_id,
        "topic": {"id": note.topic.id, "title": note.topic.title}
        if note.topic is not None
        else None,
        "created_at": serialize_timestamp(note.created_at),
        "updated_at": serialize_timestamp(note.updated_at),
    }


def internal_error(message):
    db.session.rollback()
    current_app.logger.exception("Topics API request failed.")
    return api_error("internal_error", message, 500)

# Topics API routes
@topic_bp.get("/api/topics")
def list_topics():
    """Return the signed-in user's topic summaries."""
    user_id, error_response = api_user_id()
    if error_response:
        return error_response

    try:
        topic_counts = topic_service.list_topics(user_id)
        return api_json({
            "topics": [
                serialize_topic(topic, note_count)
                for topic, note_count in topic_counts
            ]
        })
    except Exception:
        return internal_error("Unable to load topics.")


@topic_bp.get("/api/topics/<int:topic_id>")
def get_topic(topic_id):
    """Return an owned topic and its latest notes."""
    user_id, error_response = api_user_id()
    if error_response:
        return error_response

    try:
        topic = topic_service.topic_view(topic_id, user_id)
        notes = topic_service.list_topic_notes(topic.id, user_id)
        return api_json({
            "topic": serialize_topic(topic, len(notes)),
            "notes": [serialize_note_summary(note) for note in notes],
        })
    except topic_service.TopicNotFoundError:
        return api_error("not_found", "Topic not found.", 404)
    except Exception:
        return internal_error("Unable to load topic.")


@topic_bp.post("/api/topics")
def create_topic():
    """Create a topic for the signed-in user."""
    user_id, error_response = api_user_id()
    if error_response:
        return error_response

    data, error_response = topic_payload()
    if error_response:
        return error_response

    try:
        topic = topic_service.create_topic(
            user_id=user_id,
            title=data["title"],
            description=data["description"],
            color=data["color"],
        )
        return api_json({"topic": serialize_topic(topic, 0)}, 201)
    except ValueError as error:
        return api_error("validation_error", str(error), 400)
    except Exception:
        return internal_error("Unable to save topic.")


@topic_bp.patch("/api/topics/<int:topic_id>")
def update_topic(topic_id):
    """Update an owned topic's title, description, and color."""
    user_id, error_response = api_user_id()
    if error_response:
        return error_response

    data, error_response = topic_payload()
    if error_response:
        return error_response

    try:
        topic = topic_service.edit_topic(
            topic_id=topic_id,
            user_id=user_id,
            title=data["title"],
            description=data["description"],
            color=data["color"],
        )
        note_count = len(topic_service.list_topic_notes(topic.id, user_id))
        return api_json({"topic": serialize_topic(topic, note_count)})
    except topic_service.TopicNotFoundError:
        return api_error("not_found", "Topic not found.", 404)
    except ValueError as error:
        return api_error("validation_error", str(error), 400)
    except Exception:
        return internal_error("Unable to update topic.")


@topic_bp.delete("/api/topics/<int:topic_id>")
def delete_topic(topic_id):
    """Delete an owned topic only after its study data has been moved."""
    user_id, error_response = api_user_id()
    if error_response:
        return error_response

    try:
        topic_service.delete_topic(topic_id, user_id)
    except topic_service.TopicNotFoundError:
        return api_error("not_found", "Topic not found.", 404)
    except topic_service.TopicNotEmptyError as error:
        return api_error("topic_not_empty", str(error), 409)
    except Exception:
        return internal_error("Unable to delete topic.")

    response = current_app.response_class(status=204)
    response.headers["Cache-Control"] = "no-store"
    return response
