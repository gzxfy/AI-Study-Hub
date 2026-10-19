from backend import db
from backend.models.models import Message, Note, Topic, User
from backend.services import assistant_service


def create_signed_in_note(client, test_app, topic_id=None):
    with test_app.app_context():
        user = User(
            username="assistant-user",
            email="assistant@example.com",
            password_hash="not-a-real-password-hash",
        )
        db.session.add(user)
        db.session.flush()
        note = Note(
            user_id=user.id,
            topic_id=topic_id,
            title="Study note",
            content="The note content is available to the tutor.",
        )
        db.session.add(note)
        db.session.commit()
        user_id = user.id
        note_id = note.id

    with client.session_transaction() as session:
        session["user_id"] = user_id
    return note_id


def test_get_conversation_returns_json_messages(client, test_app):
    note_id = create_signed_in_note(client, test_app)

    response = client.get(f"/api/notes/{note_id}/conversation")

    assert response.status_code == 200
    assert response.json == {"messages": []}
    assert response.headers["Cache-Control"] == "no-store"


def test_send_message_returns_and_persists_exchange(client, test_app, monkeypatch):
    note_id = create_signed_in_note(client, test_app)
    calls = []

    def fake_ask_ai(question, content, history):
        calls.append((question, content, history))
        return "Tutor reply"

    monkeypatch.setattr(assistant_service, "ask_ai", fake_ask_ai)

    response = client.post(
        f"/api/notes/{note_id}/messages",
        json={"message": "  Explain this note.  ", "request_id": "attempt-1"},
    )

    assert response.status_code == 200
    assert [message["role"] for message in response.json["messages"]] == ["user", "assistant"]
    assert [message["content"] for message in response.json["messages"]] == [
        "Explain this note.",
        "Tutor reply",
    ]
    assert calls[0][0:2] == (
        "Explain this note.",
        "The note content is available to the tutor.",
    )
    assert calls[0][2] == []
    with test_app.app_context():
        persisted_messages = Message.query.order_by(Message.id.asc()).all()
        user_message, assistant_message = persisted_messages
        assert user_message.content == "Explain this note."
        assert assistant_message.role == "assistant"
        assert assistant_message.content == "Tutor reply"
        assert user_message.request_id == "attempt-1"


def test_send_message_passes_prior_exchange_to_ai(client, test_app, monkeypatch):
    note_id = create_signed_in_note(client, test_app)
    histories = []

    def fake_ask_ai(question, content, history):
        histories.append(list(history))
        return f"Reply to: {question}"

    monkeypatch.setattr(assistant_service, "ask_ai", fake_ask_ai)
    client.post(
        f"/api/notes/{note_id}/messages",
        json={"message": "First question", "request_id": "first"},
    )
    response = client.post(
        f"/api/notes/{note_id}/messages",
        json={"message": "Follow-up question", "request_id": "second"},
    )

    assert response.status_code == 200
    assert [message["content"] for message in response.json["messages"]] == [
        "First question",
        "Reply to: First question",
        "Follow-up question",
        "Reply to: Follow-up question",
    ]
    assert [message.content for message in histories[1]] == [
        "First question",
        "Reply to: First question",
    ]


def test_retrying_request_id_does_not_call_ai_twice(client, test_app, monkeypatch):
    note_id = create_signed_in_note(client, test_app)
    calls = []

    def fake_ask_ai(question, content, history):
        calls.append(question)
        return "Tutor reply"

    monkeypatch.setattr(assistant_service, "ask_ai", fake_ask_ai)
    payload = {"message": "Explain this note.", "request_id": "attempt-1"}

    first_response = client.post(f"/api/notes/{note_id}/messages", json=payload)
    retry_response = client.post(f"/api/notes/{note_id}/messages", json=payload)

    assert first_response.status_code == retry_response.status_code == 200
    assert first_response.json == retry_response.json
    assert calls == ["Explain this note."]


def test_include_topic_uses_notes_from_the_owned_topic(client, test_app, monkeypatch):
    with test_app.app_context():
        user = User(
            username="topic-assistant-user",
            email="topic-assistant@example.com",
            password_hash="not-a-real-password-hash",
        )
        db.session.add(user)
        db.session.flush()
        topic = Topic(
            user_id=user.id,
            title="Biology",
            description="",
            color="#168A72",
        )
        db.session.add(topic)
        db.session.flush()
        other_topic = Topic(
            user_id=user.id,
            title="History",
            description="",
            color="#168A72",
        )
        db.session.add(other_topic)
        db.session.flush()
        note = Note(
            user_id=user.id,
            topic_id=topic.id,
            title="Cell note",
            content="Cells have membranes.",
        )
        related_note = Note(
            user_id=user.id,
            topic_id=topic.id,
            title="DNA note",
            content="DNA stores genetic information.",
        )
        unrelated_note = Note(
            user_id=user.id,
            topic_id=other_topic.id,
            title="History note",
            content="This note belongs to another topic.",
        )
        other_user = User(
            username="other-topic-assistant-user",
            email="other-topic-assistant@example.com",
            password_hash="not-a-real-password-hash",
        )
        db.session.add(other_user)
        db.session.flush()
        other_users_note = Note(
            user_id=other_user.id,
            topic_id=topic.id,
            title="Private note",
            content="This note belongs to another user.",
        )
        db.session.add_all([note, related_note, unrelated_note, other_users_note])
        db.session.commit()
        note_id = note.id
        user_id = user.id

    with client.session_transaction() as session:
        session["user_id"] = user_id

    received_context = []

    def fake_ask_ai_with_topics(user_id, question, topic_notes, history):
        received_context.extend(note.content for note in topic_notes)
        return "Topic reply"

    monkeypatch.setattr(assistant_service, "ask_ai_with_topics", fake_ask_ai_with_topics)
    response = client.post(
        f"/api/notes/{note_id}/messages",
        json={"message": "Connect these ideas.", "include_topic": True},
    )

    assert response.status_code == 200
    assert set(received_context) == {
        "Cells have membranes.",
        "DNA stores genetic information.",
    }
    assert "This note belongs to another topic." not in received_context
    assert "This note belongs to another user." not in received_context


def test_message_validation_and_note_ownership(client, test_app):
    note_id = create_signed_in_note(client, test_app)

    invalid_response = client.post(
        f"/api/notes/{note_id}/messages",
        json={"message": "  "},
    )
    missing_note_response = client.get("/api/notes/999/conversation")

    assert invalid_response.status_code == 400
    assert invalid_response.json["error"]["code"] == "validation_error"
    assert missing_note_response.status_code == 404
    assert missing_note_response.json["error"]["code"] == "not_found"