from flask import flash, redirect, url_for, render_template, request, session, Blueprint, jsonify, current_app
from datetime import timezone
from backend import db
from backend.models import note
from backend.models.models import User, Conversation, Note, Topic, db, Message
from backend.utils.validation_helpers import login_required
from backend import csrf
import backend.services.topic_service as topic_service

topic_bp = Blueprint('topic', __name__)


# API helper functions for handling JSON responses and errors.

def json_payload():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return None, api_error("invalid_json", "Expected a JSON object.", 400)

    if (
        not isinstance(data.get("title"), str)
        or not isinstance(data.get("content"), str)
        or "topic_id" not in data
    ):
        return None, api_error(
            "invalid_fields",
            "Title and content must be strings and topic_id is required.",
            400,
        )

    topic_id = data["topic_id"]
    if topic_id is not None and (
            not isinstance(topic_id, int) or isinstance(topic_id, bool)
        ):
            return None, api_error(
                "invalid_topic",
                "topic_id must be an integer or null.",
                400,
            )
    
    return data, None


def api_json(data, status=200):
    response = jsonify(data)
    response.headers["Cache-Control"] = "no-store"
    return response, status

def internal_error(message):
    db.session.rollback()
    current_app.logger.exception("Notes API request failed.")
    return api_error("internal_error", message, 500)

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

def serialize_timestamp(value):
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    else:
        value = value.astimezone(timezone.utc)
    return value.isoformat().replace("+00:00", "Z")

def serialize_topic(topic):
    serialized = {
        "id": topic.id,
        "title": topic.title,
        "description": topic.description,
        "color": topic.color,
        "created_at": serialize_timestamp(topic.created_at),
        "updated_at": serialize_timestamp(topic.updated_at),
    }
    
    return serialized


# Creating topic
@topic_bp.post('/api/topic/create')
def topic_create():
    """Display the topic form or create a topic for the signed-in user."""
    user_id, error_response = api_user_id()
    if error_response:
        return error_response

    data, error_response = json_payload()
    if error_response:
        return error_response

    try:
        topic = topic_service.create_topic(
            user_id=user_id,
            title=data["title"],
            description=data["description"],
            color=data["color"])
    except topic_service.InvalidTopicCreation:
        return api_error(
            "Invalid Data",
            "This topic could not be created",
            400,
        )
    except ValueError as error:
        return api_error("validation_error", str(error), 400)
    except Exception:
        return internal_error("Unable to save topic")

    return api_json({"topic": serialize_topic(topic)}, 201)

#Topic Deletion
@topic_bp.delete('/api/topic/delete')
def delete_topic(topic_id):
    """Delete an owned study topic and return to the home page."""
    try:
        topic_service.delete_topic(topic_id, session.get("user_id"))
        return jsonify({
            "success": True,
            "message": "Topic deleted successfully",
        }), 204
    except ValueError as ve:
        # Return error response with a 400 Bad Request
        return jsonify({
            "success": False,
            "message": str(ve)
        }), 400


@topic_bp.patch('/api/edit/topic')
def edit_topic(topic_id):
    """Display the topic edit form or save changes to an owned topic."""
    user_id, error_response = api_user_id()
    if error_response:
        return error_response

    data, error_response = json_payload()
    if error_response:
        return error_response

    try:
        topic = topic_service.edit_topic(
            topic_id=topic_id,
            user_id=user_id,
            title=data["title"],
            description=data["description"],
            color=data["color"])
    except ValueError as ve:
        return api_error("validation_error", str(ve), 400)
    except Exception:
        return internal_error("Unable to edit topic")

    return api_json({"topic": serialize_topic(topic)}, 200)


@topic_bp.route('/api/topic/<int:topic_id>')
def topic_view(topic_id):
    """Display a topic and its notes after verifying user ownership."""
    user_id, error_response = api_user_id()
    if error_response:
        return error_response
    
    try:
        topic = topic_service.topic_view(topic_id, session.get("user_id"))
    except ValueError as ve:
        return api_error("validation_error", str(ve), 400)
    return api_json({"topic": serialize_topic(topic)}, 200)  # Return the topic data as JSON

@topic_bp.get('/api/topics')
def topics_view():
    """Return a list of topics owned by the signed-in user."""
    user_id, error_response = api_user_id()
    if error_response:
        return error_response

    try:
        topics = topic_service.list_topics(user_id)
        return api_json({
            "topics": [serialize_topic(topic) for topic in topics]
        })
    except Exception:
        return internal_error("Unable to load topics.")