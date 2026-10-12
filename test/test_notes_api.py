from datetime import datetime

import pytest

from backend import db
from backend.models.models import (
    Conversation,
    Flashcard,
    FlashcardProgress,
    Message,
    Note,
    QuizAttempt,
    QuizQuestionAttempt,
    StudyEvent,
    Topic,
    User,
)


def create_user(test_app, username="learner", email="learner@example.com"):
    with test_app.app_context():
        user = User(
            username=username,
            email=email,
            password_hash="not-used-by-these-tests",
        )
        db.session.add(user)
        db.session.commit()
        return user.id


def sign_in(client, user_id):
    with client.session_transaction() as session:
        session["user_id"] = user_id


def create_topic(test_app, user_id, title="Databases"):
    with test_app.app_context():
        topic = Topic(user_id=user_id, title=title)
        db.session.add(topic)
        db.session.commit()
        return topic.id


def test_notes_api_requires_a_valid_session(client):
    requests = (
        client.get("/api/notes"),
        client.get("/api/topics"),
        client.get("/api/notes/1"),
        client.post(
            "/api/notes",
            json={"title": "A note", "content": "Text", "topic_id": None},
        ),
    )

    for response in requests:
        assert response.status_code == 401
        assert response.json["error"]["code"] == "unauthenticated"
        assert response.headers["Cache-Control"] == "no-store"


def test_list_notes_only_returns_the_users_notes_in_updated_order(
    client, test_app
):
    user_id = create_user(test_app)
    other_user_id = create_user(
        test_app, username="other", email="other@example.com"
    )
    topic_id = create_topic(test_app, user_id)
    sign_in(client, user_id)

    with test_app.app_context():
        older_note = Note(
            user_id=user_id,
            topic_id=topic_id,
            title="Earlier",
            content="first line\nsecond line",
            created_at=datetime(2026, 10, 2, 16),
            updated_at=datetime(2026, 10, 2, 16),
        )
        newer_note = Note(
            user_id=user_id,
            title="Later",
            content="  " + "word " * 50,
            created_at=datetime(2026, 10, 3, 16),
            updated_at=datetime(2026, 10, 3, 16),
        )
        other_note = Note(
            user_id=other_user_id,
            title="Private",
            content="Must not be returned",
        )
        db.session.add_all([older_note, newer_note, other_note])
        db.session.commit()
        expected_ids = [newer_note.id, older_note.id]

    response = client.get("/api/notes")

    assert response.status_code == 200
    assert response.headers["Cache-Control"] == "no-store"
    notes = response.json["notes"]
    assert [note["id"] for note in notes] == expected_ids
    assert notes[0]["excerpt"] == "word " * 32
    assert "content" not in notes[0]
    assert notes[1]["excerpt"] == "first line second line"
    assert notes[1]["topic"] == {"id": topic_id, "title": "Databases"}
    assert notes[1]["created_at"] == "2026-10-02T16:00:00Z"
    assert notes[1]["updated_at"] == "2026-10-02T16:00:00Z"


@pytest.mark.parametrize("topic_id", [None, "owned"])
def test_create_note_persists_the_note_and_returns_contract_shape(
    client, test_app, topic_id
):
    user_id = create_user(test_app)
    owned_topic_id = create_topic(test_app, user_id)
    sign_in(client, user_id)
    assigned_topic_id = owned_topic_id if topic_id == "owned" else None

    response = client.post(
        "/api/notes",
        json={
            "title": "Normalization",
            "content": "First form.\n\nSecond form.",
            "topic_id": assigned_topic_id,
        },
    )

    assert response.status_code == 201
    assert response.headers["Cache-Control"] == "no-store"
    note_data = response.json["note"]
    assert note_data["title"] == "Normalization"
    assert note_data["content"] == "First form.\n\nSecond form."
    assert note_data["topic_id"] == assigned_topic_id
    assert note_data["topic"] == (
        {"id": owned_topic_id, "title": "Databases"}
        if assigned_topic_id is not None
        else None
    )
    assert note_data["id"] is not None
    assert note_data["created_at"].endswith("Z")
    assert note_data["updated_at"].endswith("Z")

    with test_app.app_context():
        saved_note = db.session.get(Note, note_data["id"])
        assert saved_note is not None
        assert saved_note.user_id == user_id
        assert saved_note.content == "First form.\n\nSecond form."
        assert saved_note.topic_id == assigned_topic_id


@pytest.mark.parametrize(
    ("payload", "expected_code", "expected_message"),
    [
        ({"title": "", "content": "Body", "topic_id": None},
         "validation_error", "Title is required."),
        ({"title": "Title", "content": " \n ", "topic_id": None},
         "validation_error", "Content is required."),
        ({"title": "T" * 101, "content": "Body", "topic_id": None},
         "validation_error", "Title cannot be longer than 100 characters."),
        ({"title": "Title", "content": "C" * 5001, "topic_id": None},
         "validation_error", "Content cannot be longer than 5000 characters."),
        ({"title": "Title", "content": "Body"},
         "invalid_fields", "Title and content must be strings and topic_id is required."),
    ],
)
def test_create_note_rejects_invalid_payloads(
    client, test_app, payload, expected_code, expected_message
):
    user_id = create_user(test_app)
    sign_in(client, user_id)

    response = client.post("/api/notes", json=payload)

    assert response.status_code == 400
    assert response.json["error"] == {
        "code": expected_code,
        "message": expected_message,
    }
    assert response.headers["Cache-Control"] == "no-store"
    with test_app.app_context():
        assert Note.query.count() == 0


def test_create_note_rejects_malformed_json(client, test_app):
    user_id = create_user(test_app)
    sign_in(client, user_id)

    response = client.post(
        "/api/notes",
        data='{"title":',
        content_type="application/json",
    )

    assert response.status_code == 400
    assert response.json["error"]["code"] == "invalid_json"
    assert response.headers["Cache-Control"] == "no-store"


@pytest.mark.parametrize("topic_kind", ["unknown", "other_user"])
def test_create_note_rejects_topics_the_user_does_not_own(
    client, test_app, topic_kind
):
    user_id = create_user(test_app)
    other_user_id = create_user(
        test_app, username="other", email="other@example.com"
    )
    topic_owner_id = other_user_id if topic_kind == "other_user" else user_id
    topic_id = create_topic(test_app, topic_owner_id)
    if topic_kind == "unknown":
        topic_id += 1000
    sign_in(client, user_id)

    response = client.post(
        "/api/notes",
        json={"title": "Title", "content": "Body", "topic_id": topic_id},
    )

    assert response.status_code == 400
    assert response.json["error"]["code"] == "invalid_topic"
    with test_app.app_context():
        assert Note.query.count() == 0


@pytest.mark.parametrize("topic_id", ["2", 2.5, True])
def test_create_note_rejects_non_integer_topic_ids(client, test_app, topic_id):
    user_id = create_user(test_app)
    sign_in(client, user_id)

    response = client.post(
        "/api/notes",
        json={"title": "Title", "content": "Body", "topic_id": topic_id},
    )

    assert response.status_code == 400
    assert response.json["error"]["code"] == "invalid_topic"


def test_read_note_returns_owned_note_and_hides_other_users_notes(
    client, test_app
):
    user_id = create_user(test_app)
    other_user_id = create_user(
        test_app, username="other", email="other@example.com"
    )
    with test_app.app_context():
        own_note = Note(user_id=user_id, title="Mine", content="My text")
        private_note = Note(
            user_id=other_user_id,
            title="Private",
            content="Secret text",
        )
        db.session.add_all([own_note, private_note])
        db.session.commit()
        own_note_id = own_note.id
        private_note_id = private_note.id
    sign_in(client, user_id)

    response = client.get(f"/api/notes/{own_note_id}")
    inaccessible_response = client.get(f"/api/notes/{private_note_id}")
    missing_response = client.get("/api/notes/999999")

    assert response.status_code == 200
    assert response.headers["Cache-Control"] == "no-store"
    assert response.json["note"]["title"] == "Mine"
    assert response.json["note"]["topic_id"] is None
    assert response.json["note"]["topic"] is None
    assert response.json["note"]["content"] == "My text"
    for hidden_response in (inaccessible_response, missing_response):
        assert hidden_response.status_code == 404
        assert hidden_response.json["error"]["code"] == "not_found"
        assert hidden_response.json["error"]["message"] == "Note not found."
        assert hidden_response.headers["Cache-Control"] == "no-store"


def test_update_note_persists_content_and_topic_reassignment(client, test_app):
    user_id = create_user(test_app)
    first_topic_id = create_topic(test_app, user_id, title="First topic")
    second_topic_id = create_topic(test_app, user_id, title="Second topic")
    with test_app.app_context():
        note = Note(
            user_id=user_id,
            topic_id=first_topic_id,
            title="Original",
            content="Original body",
        )
        db.session.add(note)
        db.session.commit()
        note_id = note.id
    sign_in(client, user_id)

    response = client.patch(
        f"/api/notes/{note_id}",
        json={
            "title": "  Updated title  ",
            "content": "Updated first line.\n\nUpdated second line.",
            "topic_id": second_topic_id,
            "user_id": user_id + 1,
        },
    )

    assert response.status_code == 200
    assert response.headers["Cache-Control"] == "no-store"
    assert response.json["note"]["title"] == "Updated title"
    assert response.json["note"]["content"] == "Updated first line.\n\nUpdated second line."
    assert response.json["note"]["topic_id"] == second_topic_id
    assert response.json["note"]["topic"] == {
        "id": second_topic_id,
        "title": "Second topic",
    }
    with test_app.app_context():
        saved_note = db.session.get(Note, note_id)
        assert saved_note.user_id == user_id
        assert saved_note.title == "Updated title"
        assert saved_note.content == "Updated first line.\n\nUpdated second line."
        assert saved_note.topic_id == second_topic_id

    unassigned_response = client.patch(
        f"/api/notes/{note_id}",
        json={
            "title": "Updated title",
            "content": "Updated body",
            "topic_id": None,
        },
    )
    assert unassigned_response.status_code == 200
    assert unassigned_response.json["note"]["topic_id"] is None
    assert unassigned_response.json["note"]["topic"] is None


def test_update_note_rejects_foreign_topic_and_preserves_existing_note(
    client, test_app
):
    user_id = create_user(test_app)
    other_user_id = create_user(
        test_app, username="other", email="other@example.com"
    )
    foreign_topic_id = create_topic(test_app, other_user_id)
    with test_app.app_context():
        note = Note(user_id=user_id, title="Original", content="Original body")
        db.session.add(note)
        db.session.commit()
        note_id = note.id
    sign_in(client, user_id)

    response = client.patch(
        f"/api/notes/{note_id}",
        json={
            "title": "Changed",
            "content": "Changed body",
            "topic_id": foreign_topic_id,
        },
    )

    assert response.status_code == 400
    assert response.json["error"]["code"] == "invalid_topic"
    with test_app.app_context():
        note = db.session.get(Note, note_id)
        assert note.title == "Original"
        assert note.content == "Original body"
        assert note.topic_id is None


@pytest.mark.parametrize(
    ("payload", "expected_message"),
    [
        ({"title": "", "content": "Body", "topic_id": None},
         "Title is required."),
        ({"title": "Title", "content": " ", "topic_id": None},
         "Content is required."),
        ({"title": "T" * 101, "content": "Body", "topic_id": None},
         "Title cannot be longer than 100 characters."),
        ({"title": "Title", "content": "C" * 5001, "topic_id": None},
         "Content cannot be longer than 5000 characters."),
    ],
)
def test_update_note_rejects_invalid_data_without_modifying_note(
    client, test_app, payload, expected_message
):
    user_id = create_user(test_app)
    with test_app.app_context():
        note = Note(user_id=user_id, title="Original", content="Original body")
        db.session.add(note)
        db.session.commit()
        note_id = note.id
    sign_in(client, user_id)

    response = client.patch(f"/api/notes/{note_id}", json=payload)

    assert response.status_code == 400
    assert response.json["error"]["code"] == "validation_error"
    assert response.json["error"]["message"] == expected_message
    with test_app.app_context():
        note = db.session.get(Note, note_id)
        assert note.title == "Original"
        assert note.content == "Original body"


def test_update_and_delete_note_hide_missing_and_foreign_notes(
    client, test_app
):
    user_id = create_user(test_app)
    other_user_id = create_user(
        test_app, username="other", email="other@example.com"
    )
    with test_app.app_context():
        note = Note(
            user_id=other_user_id,
            title="Private",
            content="Do not modify or delete",
        )
        db.session.add(note)
        db.session.commit()
        foreign_note_id = note.id
    sign_in(client, user_id)
    payload = {"title": "Attempt", "content": "Attempt", "topic_id": None}

    for note_id in (foreign_note_id, 999999):
        update_response = client.patch(f"/api/notes/{note_id}", json=payload)
        delete_response = client.delete(f"/api/notes/{note_id}")
        assert update_response.status_code == 404
        assert update_response.json["error"]["code"] == "not_found"
        assert delete_response.status_code == 404
        assert delete_response.json["error"]["code"] == "not_found"
    with test_app.app_context():
        note = db.session.get(Note, foreign_note_id)
        assert note.title == "Private"
        assert note.content == "Do not modify or delete"


def test_delete_note_removes_note_and_dependent_study_data_only(
    client, test_app
):
    user_id = create_user(test_app)
    other_user_id = create_user(
        test_app, username="other", email="other@example.com"
    )
    topic_id = create_topic(test_app, user_id)
    with test_app.app_context():
        note = Note(
            user_id=user_id,
            topic_id=topic_id,
            title="To delete",
            content="Note body",
        )
        other_note = Note(
            user_id=other_user_id,
            title="Keep",
            content="Unrelated note",
        )
        db.session.add_all([note, other_note])
        db.session.flush()
        flashcard = Flashcard(
            user_id=user_id,
            topic_id=topic_id,
            note_id=note.id,
            question="Question",
            answer="Answer",
        )
        conversation = Conversation(user_id=user_id, note_id=note.id)
        quiz_attempt = QuizAttempt(user_id=user_id, note_id=note.id)
        db.session.add_all([flashcard, conversation, quiz_attempt])
        db.session.flush()
        progress = FlashcardProgress(
            user_id=user_id,
            flashcard_id=flashcard.id,
        )
        event = StudyEvent(
            user_id=user_id,
            flashcard_id=flashcard.id,
            is_correct=True,
        )
        message = Message(
            conversation_id=conversation.id,
            role="assistant",
            content="Review",
        )
        question_attempt = QuizQuestionAttempt(
            quiz_attempt_id=quiz_attempt.id,
            flashcard_id=flashcard.id,
            user_answer="Answer",
            correct_answer="Answer",
            is_correct=True,
        )
        db.session.add_all([progress, event, message, question_attempt])
        db.session.commit()
        note_id = note.id
        other_note_id = other_note.id
        flashcard_id = flashcard.id
        conversation_id = conversation.id
        quiz_attempt_id = quiz_attempt.id
        progress_id = progress.id
        event_id = event.id
        message_id = message.id
        question_attempt_id = question_attempt.id
    sign_in(client, user_id)

    response = client.delete(f"/api/notes/{note_id}")

    assert response.status_code == 204
    assert response.data == b""
    assert response.headers["Cache-Control"] == "no-store"
    with test_app.app_context():
        assert db.session.get(Note, note_id) is None
        assert db.session.get(Note, other_note_id) is not None
        for model, record_id in (
            (Flashcard, flashcard_id),
            (FlashcardProgress, progress_id),
            (StudyEvent, event_id),
            (Conversation, conversation_id),
            (Message, message_id),
            (QuizAttempt, quiz_attempt_id),
            (QuizQuestionAttempt, question_attempt_id),
        ):
            assert db.session.get(model, record_id) is None
        assert db.session.get(Topic, topic_id) is not None


def test_note_update_and_delete_require_csrf(client, test_app):
    user_id = create_user(test_app)
    with test_app.app_context():
        note = Note(user_id=user_id, title="Title", content="Body")
        db.session.add(note)
        db.session.commit()
        note_id = note.id
    sign_in(client, user_id)
    test_app.config["WTF_CSRF_ENABLED"] = True

    missing_token_responses = (
        client.patch(
            f"/api/notes/{note_id}",
            json={"title": "Updated", "content": "Body", "topic_id": None},
        ),
        client.delete(f"/api/notes/{note_id}"),
    )
    token_response = client.get("/api/auth/csrf")
    headers = {"X-CSRFToken": token_response.json["csrf_token"]}
    update_response = client.patch(
        f"/api/notes/{note_id}",
        json={"title": "Updated", "content": "Body", "topic_id": None},
        headers=headers,
    )
    delete_response = client.delete(f"/api/notes/{note_id}", headers=headers)

    for response in missing_token_responses:
        assert response.status_code == 400
        assert response.json["error"]["code"] == "csrf_failed"
        assert response.headers["Cache-Control"] == "no-store"
    assert update_response.status_code == 200
    assert delete_response.status_code == 204


def test_note_mutation_enforces_csrf_and_returns_no_store_errors(
    client, test_app
):
    user_id = create_user(test_app)
    sign_in(client, user_id)
    test_app.config["WTF_CSRF_ENABLED"] = True

    missing_token_response = client.post(
        "/api/notes",
        json={"title": "Title", "content": "Body", "topic_id": None},
    )
    token_response = client.get("/api/auth/csrf")
    valid_response = client.post(
        "/api/notes",
        json={"title": "Title", "content": "Body", "topic_id": None},
        headers={"X-CSRFToken": token_response.json["csrf_token"]},
    )

    assert missing_token_response.status_code == 400
    assert missing_token_response.json["error"]["code"] == "csrf_failed"
    assert missing_token_response.headers["Cache-Control"] == "no-store"
    assert valid_response.status_code == 201


def test_unexpected_note_read_errors_are_logged_and_sanitized(
    client, test_app, monkeypatch
):
    user_id = create_user(test_app)
    sign_in(client, user_id)

    def fail_to_list_notes(user_id):
        assert user_id is not None
        raise RuntimeError("database credentials must not be exposed")

    monkeypatch.setattr(
        "backend.services.note_service.list_notes",
        fail_to_list_notes,
    )
    response = client.get("/api/notes")

    assert response.status_code == 500
    assert response.json["error"] == {
        "code": "internal_error",
        "message": "Unable to load notes.",
    }
    assert "database credentials" not in response.get_data(as_text=True)
    assert response.headers["Cache-Control"] == "no-store"
