from app import db
from app.models.models import Topic, db
import app.utils.validation_helpers as validation_helpers


def create_topic(user_id, title, description, color):
    """Validate and save a topic that organizes a user's study materials."""
    validation_helpers.validate_topic_data(title, description, color)
    new_topic = Topic(user_id=user_id, title=title, description=description, color=color)
    db.session.add(new_topic)
    db.session.commit()
    return new_topic

def delete_topic(topic_id, user_id):
    """Delete a topic after confirming that the requesting user owns it."""
    topic = Topic.query.get_or_404(topic_id)
    if not topic:
        raise ValueError("Topic not found!")
    if topic.user_id != user_id:
        raise ValueError("You do not have permission to delete this topic!")
    db.session.delete(topic)
    db.session.commit()

def edit_topic(topic_id, user_id, title, description, color):
    """Validate and update the title, description, and color of an owned topic."""
    topic = Topic.query.get_or_404(topic_id)
    if not topic:
        raise ValueError("Topic not found!")
    if topic.user_id != user_id:
        raise ValueError("You do not have permission to edit this topic!")
    validation_helpers.validate_topic_data(title, description, color)
    topic.title = title
    topic.description = description
    topic.color = color
    db.session.commit()
    return topic

def topic_view(topic_id, user_id):
    """Return a topic after verifying that it belongs to the requesting user."""
    topic = Topic.query.get_or_404(topic_id)
    if not topic:
        raise ValueError("Topic not found!")
    if topic.user_id != user_id:
        raise ValueError("You do not have permission to view this topic!")
    return topic