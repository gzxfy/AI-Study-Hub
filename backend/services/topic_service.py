from sqlalchemy import and_, delete, func

from backend import db
from backend.models.models import Flashcard, Note, Progress, QuizAttempt, Topic
import backend.utils.validation_helpers as validation_helpers


class TopicNotFoundError(ValueError):
    """Raised when a topic does not exist or is not owned by the user."""


class TopicNotEmptyError(ValueError):
    """Raised when study data is still linked to a topic."""


def _owned_topic(topic_id, user_id, lock=False):
    query = Topic.query.filter_by(id=topic_id, user_id=user_id)
    if lock:
        query = query.with_for_update()
    topic = query.first()
    if topic is None:
        raise TopicNotFoundError("Topic not found.")
    return topic


def create_topic(user_id, title, description, color):
    """Validate and save a topic that organizes a user's study materials."""
    validation_helpers.validate_topic_data(title, description, color)
    topic = Topic(
        user_id=user_id,
        title=title.strip(),
        description=description.strip(),
        color=color,
    )
    db.session.add(topic)
    db.session.commit()
    return topic


def list_topics(user_id):
    """Return owned topics with note counts, sorted by title."""
    return (
        db.session.query(Topic, func.count(Note.id))
        .outerjoin(
            Note,
            and_(Note.topic_id == Topic.id, Note.user_id == user_id),
        )
        .filter(Topic.user_id == user_id)
        .group_by(Topic.id)
        .order_by(Topic.title.asc(), Topic.id.asc())
        .all()
    )


def topic_belongs_to_user(topic_id, user_id):
    """Check that a topic exists and belongs to the requesting user."""
    return (
        Topic.query.filter_by(id=topic_id, user_id=user_id).first()
        is not None
    )


def topic_view(topic_id, user_id):
    """Return a topic after verifying ownership."""
    return _owned_topic(topic_id, user_id)


def list_topic_notes(topic_id, user_id):
    """Return a topic's notes for its owner, newest updates first."""
    return (
        Note.query
        .filter_by(topic_id=topic_id, user_id=user_id)
        .order_by(Note.updated_at.desc(), Note.id.desc())
        .all()
    )


def edit_topic(topic_id, user_id, title, description, color):
    """Validate and update an owned topic."""
    topic = _owned_topic(topic_id, user_id, lock=True)
    validation_helpers.validate_topic_data(title, description, color)
    topic.title = title.strip()
    topic.description = description.strip()
    topic.color = color
    db.session.commit()
    return topic


def delete_topic(topic_id, user_id):
    """Delete an owned topic only when no study data references it."""
    if db.engine.dialect.name == "sqlite":
        # SQLite ignores SELECT FOR UPDATE; reserve writes before checking references.
        db.session.commit()
        db.session.execute(db.text("BEGIN IMMEDIATE"))

    topic = _owned_topic(topic_id, user_id, lock=True)
    has_references = any((
        Note.query.filter_by(topic_id=topic.id).first(),
        Flashcard.query.filter_by(topic_id=topic.id).first(),
        Progress.query.filter_by(topic_id=topic.id).first(),
        QuizAttempt.query.filter_by(topic_id=topic.id).first(),
    ))
    if has_references:
        raise TopicNotEmptyError(
            "Move this topic's notes and other study data before deleting it."
        )

    # Use a bulk delete so the model's ORM delete-orphan cascades cannot remove data.
    result = db.session.execute(
        delete(Topic)
        .where(Topic.id == topic.id, Topic.user_id == user_id)
        .execution_options(synchronize_session=False)
    )
    if result.rowcount != 1:
        raise TopicNotFoundError("Topic not found.")
    db.session.commit()
