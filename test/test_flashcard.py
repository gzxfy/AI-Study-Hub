import pytest

from backend import db
from backend.models.models import Flashcard, Note, Topic, User


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


def create_note(test_app, user_id, topic_id=None, title="Study note"):
    with test_app.app_context():
        note = Note(
            user_id=user_id,
            topic_id=topic_id,
            title=title,
            content="Notes used to review this topic.",
        )
        db.session.add(note)
        db.session.commit()
        return note.id


def create_flashcard(
    test_app,
    user_id,
    note_id,
    topic_id=None,
    question="What is normalization?",
    answer="A way to organize relational data.",
    difficulty="medium",
):
    with test_app.app_context():
        flashcard = Flashcard(
            user_id=user_id,
            note_id=note_id,
            topic_id=topic_id,
            question=question,
            answer=answer,
            difficulty=difficulty,
        )
        db.session.add(flashcard)
        db.session.commit()
        return flashcard.id


def flashcard_payload(note_id, **overrides):
    payload = {
        "note_id": note_id,
        "question": "What is normalization?",
        "answer": "A way to organize relational data.",
        "difficulty": "medium",
    }
    payload.update(overrides)
    return payload


def test_flashcard_routes_require_a_valid_session(client, test_app):
    responses = (
        client.get("/api/flashcards"),
        client.get("/api/flashcards/1"),
        client.post("/api/flashcards", json=flashcard_payload(1)),
        client.patch("/api/flashcards/1", json={"question": "Updated", "answer": "Answer"}),
        client.delete("/api/flashcards/1"),
    )

    for response in responses:
        assert response.status_code == 401
        assert response.json["error"]["code"] == "unauthenticated"
        assert response.headers["Cache-Control"] == "no-store"

    sign_in(client, 999)
    stale_session_response = client.get("/api/flashcards")
    assert stale_session_response.status_code == 401
    assert stale_session_response.json["error"]["code"] == "unauthenticated"


@pytest.mark.parametrize("with_topic", [False, True])
def test_create_flashcard_persists_data_and_returns_contract_shape(
    client, test_app, with_topic
):
    user_id = create_user(test_app)
    topic_id = None
    if with_topic:
        with test_app.app_context():
            topic = Topic(user_id=user_id, title="Databases")
            db.session.add(topic)
            db.session.commit()
            topic_id = topic.id
    note_id = create_note(test_app, user_id, topic_id)
    sign_in(client, user_id)

    response = client.post(
        "/api/flashcards",
        json=flashcard_payload(
            note_id,
            topic_id=topic_id,
            user_id=user_id + 1,
        ),
    )

    assert response.status_code == 201
    assert response.headers["Cache-Control"] == "no-store"
    flashcard_data = response.json["flashcard"]
    assert set(flashcard_data) == {
        "id",
        "note_id",
        "topic_id",
        "question",
        "answer",
        "difficulty",
        "created_at",
        "updated_at",
    }
    assert flashcard_data["note_id"] == note_id
    assert flashcard_data["topic_id"] == topic_id
    assert flashcard_data["question"] == "What is normalization?"
    assert flashcard_data["answer"] == "A way to organize relational data."
    assert flashcard_data["difficulty"] == "medium"
    assert flashcard_data["created_at"].endswith("Z")
    assert flashcard_data["updated_at"].endswith("Z")

    with test_app.app_context():
        saved_flashcard = db.session.get(Flashcard, flashcard_data["id"])
        assert saved_flashcard is not None
        assert saved_flashcard.user_id == user_id
        assert saved_flashcard.note_id == note_id
        assert saved_flashcard.topic_id == topic_id


@pytest.mark.parametrize(
    ("payload", "expected_code"),
    [
        ({"note_id": 1, "answer": "Answer"}, "invalid_fields"),
        ({"note_id": 1, "question": "Question", "answer": 1}, "invalid_fields"),
        ({"question": "Question", "answer": "Answer"}, "invalid_note"),
        (flashcard_payload(None), "invalid_note"),
        (flashcard_payload("1"), "invalid_note"),
        (flashcard_payload(True), "invalid_note"),
        (flashcard_payload(1, difficulty="impossible"), "validation_error"),
        (flashcard_payload(1, question="   "), "validation_error"),
        (flashcard_payload(1, answer="   "), "validation_error"),
        (flashcard_payload(1, question="Q" * 501), "validation_error"),
        (flashcard_payload(1, answer="A" * 2001), "validation_error"),
    ],
)
def test_create_flashcard_rejects_invalid_payloads(
    client, test_app, payload, expected_code
):
    user_id = create_user(test_app)
    note_id = create_note(test_app, user_id)
    sign_in(client, user_id)
    if type(payload.get("note_id")) is int and payload["note_id"] == 1:
        payload = {**payload, "note_id": note_id}

    response = client.post("/api/flashcards", json=payload)

    assert response.status_code == 400
    assert response.json["error"]["code"] == expected_code
    assert response.headers["Cache-Control"] == "no-store"
    with test_app.app_context():
        assert Flashcard.query.count() == 0


def test_create_flashcard_rejects_malformed_json(client, test_app):
    user_id = create_user(test_app)
    sign_in(client, user_id)

    response = client.post(
        "/api/flashcards",
        data='{"note_id":',
        content_type="application/json",
    )

    assert response.status_code == 400
    assert response.json["error"]["code"] == "invalid_json"


def test_create_flashcard_rejects_a_note_owned_by_another_user(client, test_app):
    user_id = create_user(test_app)
    other_user_id = create_user(
        test_app, username="other", email="other@example.com"
    )
    other_note_id = create_note(test_app, other_user_id)
    sign_in(client, user_id)

    response = client.post(
        "/api/flashcards",
        json=flashcard_payload(other_note_id),
    )

    assert response.status_code == 400
    assert response.json["error"]["code"] == "validation_error"
    with test_app.app_context():
        assert Flashcard.query.count() == 0


def test_list_flashcards_returns_only_the_users_flashcards(client, test_app):
    user_id = create_user(test_app)
    other_user_id = create_user(
        test_app, username="other", email="other@example.com"
    )
    own_note_id = create_note(test_app, user_id)
    other_note_id = create_note(test_app, other_user_id)
    first_id = create_flashcard(test_app, user_id, own_note_id, question="First")
    second_id = create_flashcard(test_app, user_id, own_note_id, question="Second")
    create_flashcard(test_app, other_user_id, other_note_id, question="Private")
    sign_in(client, user_id)

    response = client.get("/api/flashcards")

    assert response.status_code == 200
    assert response.headers["Cache-Control"] == "no-store"
    assert {card["id"] for card in response.json["flashcards"]} == {
        first_id,
        second_id,
    }
    assert {card["question"] for card in response.json["flashcards"]} == {
        "First",
        "Second",
    }


def test_get_flashcard_returns_owned_card_and_hides_other_users_cards(
    client, test_app
):
    user_id = create_user(test_app)
    other_user_id = create_user(
        test_app, username="other", email="other@example.com"
    )
    own_note_id = create_note(test_app, user_id)
    other_note_id = create_note(test_app, other_user_id)
    own_flashcard_id = create_flashcard(test_app, user_id, own_note_id)
    other_flashcard_id = create_flashcard(test_app, other_user_id, other_note_id)
    sign_in(client, user_id)

    response = client.get(f"/api/flashcards/{own_flashcard_id}")
    private_response = client.get(f"/api/flashcards/{other_flashcard_id}")
    missing_response = client.get("/api/flashcards/999999")

    assert response.status_code == 200
    assert response.json["flashcard"]["id"] == own_flashcard_id
    for hidden_response in (private_response, missing_response):
        assert hidden_response.status_code == 404
        assert hidden_response.json["error"]["code"] == "not_found"


def test_update_flashcard_persists_question_answer_and_difficulty(
    client, test_app
):
    user_id = create_user(test_app)
    note_id = create_note(test_app, user_id)
    flashcard_id = create_flashcard(test_app, user_id, note_id)
    sign_in(client, user_id)

    response = client.patch(
        f"/api/flashcards/{flashcard_id}",
        json={
            "question": "Updated question",
            "answer": "Updated answer",
            "difficulty": "hard",
        },
    )

    assert response.status_code == 200
    assert response.json["flashcard"]["question"] == "Updated question"
    assert response.json["flashcard"]["answer"] == "Updated answer"
    assert response.json["flashcard"]["difficulty"] == "hard"
    with test_app.app_context():
        saved_flashcard = db.session.get(Flashcard, flashcard_id)
        assert saved_flashcard.question == "Updated question"
        assert saved_flashcard.answer == "Updated answer"
        assert saved_flashcard.difficulty == "hard"


def test_delete_flashcard_removes_owned_card(client, test_app):
    user_id = create_user(test_app)
    note_id = create_note(test_app, user_id)
    flashcard_id = create_flashcard(test_app, user_id, note_id)
    sign_in(client, user_id)

    response = client.delete(f"/api/flashcards/{flashcard_id}")

    assert response.status_code == 204
    assert response.data == b""
    assert response.headers["Cache-Control"] == "no-store"
    with test_app.app_context():
        assert db.session.get(Flashcard, flashcard_id) is None


def test_delete_flashcard_does_not_delete_another_users_card(client, test_app):
    user_id = create_user(test_app)
    other_user_id = create_user(
        test_app, username="other", email="other@example.com"
    )
    other_note_id = create_note(test_app, other_user_id)
    other_flashcard_id = create_flashcard(
        test_app, other_user_id, other_note_id
    )
    sign_in(client, user_id)

    response = client.delete(f"/api/flashcards/{other_flashcard_id}")

    assert response.status_code == 400
    with test_app.app_context():
        assert db.session.get(Flashcard, other_flashcard_id) is not None