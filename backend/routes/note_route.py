from datetime import timezone

from flask import (Blueprint, current_app, flash, jsonify, redirect, render_template, request, session, url_for)

from backend import csrf, db
from backend.models.models import Note, User
from backend.utils.validation_helpers import login_required
import backend.services.note_service as note_service

note_bp = Blueprint('note', __name__)

# API helper functions for handling JSON responses and errors.
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


def serialize_note(note, include_content=True):
    content = note.content
    serialized = {
        "id": note.id,
        "title": note.title,
        "topic_id": note.topic_id,
        "topic": serialize_topic(note.topic),
        "created_at": serialize_timestamp(note.created_at),
        "updated_at": serialize_timestamp(note.updated_at),
    }
    if include_content:
        serialized["content"] = content
    else:
        serialized["excerpt"] = " ".join(content.split())[:160]
    return serialized


def internal_error(message):
    db.session.rollback()
    current_app.logger.exception("Notes API request failed.")
    return api_error("internal_error", message, 500)


@note_bp.get("/api/notes")
def list_notes():
    user_id, error_response = api_user_id()
    if error_response:
        return error_response

    try:
        notes = note_service.list_notes(user_id)
        return api_json({
            "notes": [serialize_note(note, include_content=False) for note in notes]
        })
    except Exception:
        return internal_error("Unable to load notes.")


@note_bp.get("/api/topics")
def list_note_topics():
    user_id, error_response = api_user_id()
    if error_response:
        return error_response

    try:
        topics = note_service.list_topics(user_id)
        return api_json({
            "topics": [{"id": topic.id, "title": topic.title} for topic in topics]
        })
    except Exception:
        return internal_error("Unable to load topics.")


@note_bp.post("/api/notes")
def api_create_note():
    user_id, error_response = api_user_id()
    if error_response:
        return error_response

    data, error_response = json_payload()
    if error_response:
        return error_response

    try:
        topic_id = data["topic_id"]
        if topic_id is not None and not note_service.topic_belongs_to_user(
            topic_id, user_id
        ):
            return api_error(
                "invalid_topic",
                "Topic is invalid or unavailable.",
                400,
            )

        note = note_service.create_note(
            user_id=user_id,
            title=data["title"],
            content=data["content"],
            topic_id=topic_id,
        )
    except note_service.InvalidTopicError:
        return api_error(
            "invalid_topic",
            "Topic is invalid or unavailable.",
            400,
        )
    except ValueError as error:
        return api_error("validation_error", str(error), 400)
    except Exception:
        return internal_error("Unable to save note.")

    return api_json({"note": serialize_note(note)}, 201)


@note_bp.get("/api/notes/<int:note_id>")
def api_view_note(note_id):
    user_id, error_response = api_user_id()
    if error_response:
        return error_response

    try:
        note = note_service.view_note(note_id, user_id)
    except ValueError:
        return api_error("not_found", "Note not found.", 404)
    except Exception:
        return internal_error("Unable to load note.")

    return api_json({"note": serialize_note(note)})