import pytest

from backend import db
from backend.models.models import Note, Topic, User
from backend.services import note_service


def create_user(test_app, username, email):
    with test_app.app_context():
        user = User(
            username=username,
            email=email,
            password_hash="not-used-by-these-tests",
        )
        db.session.add(user)
        db.session.commit()
        return user.id


def test_create_note_without_topic(test_app):
    user_id = create_user(test_app, "note-owner", "note-owner@example.com")

    with test_app.app_context():
        note = note_service.create_note(
            user_id=user_id,
            title="Study note",
            content="Saved note content.",
            topic_id=None,
        )

        assert note.id is not None
        assert note.user_id == user_id
        assert note.topic_id is None
        assert note.title == "Study note"


def test_create_note_with_owned_topic(test_app):
    user_id = create_user(test_app, "topic-owner", "topic-owner@example.com")

    with test_app.app_context():
        topic = Topic(
            user_id=user_id,
            title="Biology",
            description="Study of living things.",
            color="#168A72",
        )
        db.session.add(topic)
        db.session.commit()
        topic_id = topic.id

        note = note_service.create_note(
            user_id=user_id,
            title="Cell structure",
            content="Cells contain organelles.",
            topic_id=topic_id,
        )

        assert note.user_id == user_id
        assert note.topic_id == topic_id
        assert Note.query.filter_by(topic_id=topic_id).count() == 1


def test_create_note_rejects_topic_owned_by_another_user(test_app):
    user_id = create_user(test_app, "note-owner", "note-owner@example.com")
    other_user_id = create_user(test_app, "topic-owner", "topic-owner@example.com")

    with test_app.app_context():
        topic = Topic(
            user_id=other_user_id,
            title="Private topic",
            description="Not available to this user.",
            color="#168A72",
        )
        db.session.add(topic)
        db.session.commit()

        with pytest.raises(note_service.InvalidTopicError):
            note_service.create_note(
                user_id=user_id,
                title="Unauthorized note",
                content="This should not be saved.",
                topic_id=topic.id,
            )

        assert Note.query.count() == 0