
from types import SimpleNamespace
from unittest.mock import Mock

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

# new creation with postgres
def create_user_postgres(postgres_app, username, email):
    with postgres_app.app_context():
        user = User(
            username=username,
            email=email,
            password_hash="not-used-by-these-tests!!",
        )
        db.session.add(user)
        db.session.commit()
        return user.id

def test_create_note_without_topic_postgres(postgres_app):
    user_id = create_user_postgres(postgres_app, "note-owner", "note-owner@example.com")

    with postgres_app.app_context():
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
        assert note.content == "Saved note content."

def test_create_note_route_without_topic_postgres(postgres_app):
    client = postgres_app.test_client()
    user_id = create_user_postgres(postgres_app, "note-owner", "note-owner@example.com")

    with client.session_transaction() as session:
        session["user_id"] = user_id

    with postgres_app.app_context():
        response = client.post(
            "/api/notes",
            json={
                "title": "Study note",
                "content": "Saved note content.",
                "topic_id": None,
            },
        )

        assert response.status_code == 201, response.get_json()
        note_id = response.json["note"]["id"]

    saved = client.get(f"/api/notes/{note_id}")
    assert saved.status_code == 200, saved.get_json()
    assert saved.json["note"]["title"] == "Study note"
    assert saved.json["note"]["content"] == "Saved note content."


def test_create_note_rejects_unreadable_pdf_before_saving(monkeypatch):
    session = Mock()
    monkeypatch.setattr(note_service, "db", SimpleNamespace(session=session))
    monkeypatch.setattr(note_service.pdf_service, "extract_text_from_pdf", lambda upload: ("  ", 1))
    upload = SimpleNamespace(filename="unreadable.pdf")

    with pytest.raises(ValueError, match="empty or could not be read"):
        note_service.create_note(1, "PDF notes", "", None, uploaded_pdf_path=upload)

    session.add.assert_not_called()
    session.commit.assert_not_called()


def test_update_note_rejects_another_users_note_without_saving(monkeypatch):
    note = SimpleNamespace(user_id=1, title="Original", content="Original content", topic_id=None)
    session = Mock()
    session.get.return_value = note
    monkeypatch.setattr(note_service, "db", SimpleNamespace(session=session))

    with pytest.raises(note_service.NoteNotFoundError):
        note_service.update_note(10, 2, "Changed", "Changed content", 5)

    assert (note.title, note.content, note.topic_id) == ("Original", "Original content", None)
    session.commit.assert_not_called()


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
