from datetime import datetime

import pytest

from backend import db
from backend.models.models import Flashcard, Note, Progress, QuizAttempt, Topic, User


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


def create_topic(test_app, user_id, title="Databases", **fields):
    with test_app.app_context():
        topic = Topic(
            user_id=user_id,
            title=title,
            description=fields.get("description", "Database concepts"),
            color=fields.get("color", "#087f65"),
        )
        db.session.add(topic)
        db.session.commit()
        return topic.id


def topic_payload(**overrides):
    payload = {
        "title": "Databases",
        "description": " Relational design and SQL. ",
        "color": "#087f65",
    }
    payload.update(overrides)
    return payload


def test_topic_routes_require_an_existing_authenticated_user(client):
    anonymous_responses = (
        client.get("/api/topics"),
        client.get("/api/topics/1"),
        client.post("/api/topics", json=topic_payload()),
        client.patch("/api/topics/1", json=topic_payload()),
        client.delete("/api/topics/1"),
    )
    for response in anonymous_responses:
        assert response.status_code == 401
        assert response.json["error"]["code"] == "unauthenticated"
        assert response.headers["Cache-Control"] == "no-store"

    sign_in(client, 999)
    stale_session_response = client.get("/api/topics")
    assert stale_session_response.status_code == 401
    assert stale_session_response.json["error"]["code"] == "unauthenticated"


def test_list_topics_returns_only_owned_topics_with_note_counts_and_utc_dates(
    client, test_app
):
    user_id = create_user(test_app)
    other_user_id = create_user(
        test_app, username="other", email="other@example.com"
    )
    z_topic_id = create_topic(test_app, user_id, "Zoology")
    a_topic_id = create_topic(test_app, user_id, "Algebra")
    create_topic(test_app, other_user_id, "Private topic")
    with test_app.app_context():
        db.session.add_all([
            Note(
                user_id=user_id,
                topic_id=a_topic_id,
                title="Algebra note",
                content="Owned note",
                created_at=datetime(2026, 10, 4, 16),
                updated_at=datetime(2026, 10, 4, 16),
            ),
            Note(
                user_id=other_user_id,
                topic_id=a_topic_id,
                title="Foreign note",
                content="Must not affect this user's count",
            ),
        ])
        db.session.commit()
    sign_in(client, user_id)

    response = client.get("/api/topics")

    assert response.status_code == 200
    assert response.headers["Cache-Control"] == "no-store"
    algebra, zoology = response.json["topics"]
    assert [algebra["id"], zoology["id"]] == [a_topic_id, z_topic_id]
    with test_app.app_context():
        algebra_topic = db.session.get(Topic, a_topic_id)
    assert algebra == {
        "id": a_topic_id,
        "title": "Algebra",
        "description": "Database concepts",
        "color": "#087f65",
        "note_count": 1,
        "created_at": algebra_topic.created_at.isoformat() + "Z",
        "updated_at": algebra_topic.updated_at.isoformat() + "Z",
    }
    assert algebra["created_at"].endswith("Z")
    assert algebra["updated_at"].endswith("Z")
    assert zoology["note_count"] == 0
    assert [topic["title"] for topic in response.json["topics"]] == [
        "Algebra",
        "Zoology",
    ]


def test_list_topics_returns_empty_array_for_an_empty_library(client, test_app):
    user_id = create_user(test_app)
    sign_in(client, user_id)

    response = client.get("/api/topics")

    assert response.status_code == 200
    assert response.json == {"topics": []}


def test_create_topic_persists_normalized_data_and_ignores_client_ownership(
    client, test_app
):
    user_id = create_user(test_app)
    sign_in(client, user_id)

    response = client.post(
        "/api/topics",
        json={
            **topic_payload(),
            "user_id": user_id + 100,
            "note_count": 900,
        },
    )

    assert response.status_code == 201
    assert response.headers["Cache-Control"] == "no-store"
    topic_data = response.json["topic"]
    assert topic_data["title"] == "Databases"
    assert topic_data["description"] == "Relational design and SQL."
    assert topic_data["color"] == "#087f65"
    assert topic_data["note_count"] == 0
    assert topic_data["created_at"].endswith("Z")
    assert topic_data["updated_at"].endswith("Z")
    with test_app.app_context():
        topic = db.session.get(Topic, topic_data["id"])
        assert topic is not None
        assert topic.user_id == user_id
        assert topic.title == topic_data["title"]
        assert topic.description == topic_data["description"]


@pytest.mark.parametrize(
    ("payload", "expected_code", "expected_message"),
    [
        (None, "invalid_json", "Expected a JSON object."),
        ({"title": "A topic"}, "invalid_fields",
         "Title, description, and color must be strings."),
        (topic_payload(title="   "), "validation_error", "Title is required."),
        (topic_payload(description=" \n "), "validation_error",
         "Description is required."),
        (topic_payload(title="T" * 101), "validation_error",
         "Title cannot be longer than 100 characters."),
        (topic_payload(description="D" * 1001), "validation_error",
         "Description cannot be longer than 1000 characters."),
        (topic_payload(color="green"), "validation_error",
         "Color must be a six-digit hex color."),
        (topic_payload(color="#12345g"), "validation_error",
         "Color must be a six-digit hex color."),
    ],
)
def test_create_topic_rejects_invalid_payload_without_writing(
    client, test_app, payload, expected_code, expected_message
):
    user_id = create_user(test_app)
    sign_in(client, user_id)

    if payload is None:
        response = client.post(
            "/api/topics",
            data='{"title":',
            content_type="application/json",
        )
    else:
        response = client.post("/api/topics", json=payload)

    assert response.status_code == 400
    assert response.json["error"] == {
        "code": expected_code,
        "message": expected_message,
    }
    assert response.headers["Cache-Control"] == "no-store"
    with test_app.app_context():
        assert Topic.query.count() == 0


def test_get_topic_returns_only_its_owners_notes_in_updated_order(
    client, test_app
):
    user_id = create_user(test_app)
    other_user_id = create_user(
        test_app, username="other", email="other@example.com"
    )
    topic_id = create_topic(test_app, user_id)
    with test_app.app_context():
        older = Note(
            user_id=user_id,
            topic_id=topic_id,
            title="Older",
            content="older note content",
            created_at=datetime(2026, 10, 3, 16),
            updated_at=datetime(2026, 10, 3, 16),
        )
        newer = Note(
            user_id=user_id,
            topic_id=topic_id,
            title="Newer",
            content="newest note content",
            created_at=datetime(2026, 10, 4, 16),
            updated_at=datetime(2026, 10, 4, 16),
        )
        foreign_note = Note(
            user_id=other_user_id,
            topic_id=topic_id,
            title="Foreign",
            content="another account's note",
        )
        db.session.add_all([older, newer, foreign_note])
        db.session.commit()
        expected_ids = [newer.id, older.id]
    sign_in(client, user_id)

    response = client.get(f"/api/topics/{topic_id}")

    assert response.status_code == 200
    assert response.headers["Cache-Control"] == "no-store"
    assert response.json["topic"]["id"] == topic_id
    assert response.json["topic"]["note_count"] == 2
    notes = response.json["notes"]
    assert [note["id"] for note in notes] == expected_ids
    assert [note["title"] for note in notes] == ["Newer", "Older"]
    assert notes[0]["excerpt"] == "newest note content"
    assert notes[0]["topic"] == {"id": topic_id, "title": "Databases"}
    assert notes[0]["created_at"] == "2026-10-04T16:00:00Z"


def test_get_topic_returns_empty_notes_for_a_topic_without_notes(
    client, test_app
):
    user_id = create_user(test_app)
    topic_id = create_topic(test_app, user_id)
    sign_in(client, user_id)

    response = client.get(f"/api/topics/{topic_id}")

    assert response.status_code == 200
    assert response.json["topic"]["note_count"] == 0
    assert response.json["notes"] == []


@pytest.mark.parametrize("topic_owner", ["missing", "another_user"])
def test_get_topic_hides_missing_and_other_users_topics(
    client, test_app, topic_owner
):
    user_id = create_user(test_app)
    other_user_id = create_user(
        test_app, username="other", email="other@example.com"
    )
    topic_id = create_topic(
        test_app, other_user_id if topic_owner == "another_user" else user_id
    )
    if topic_owner == "missing":
        topic_id += 1000
    sign_in(client, user_id)

    response = client.get(f"/api/topics/{topic_id}")

    assert response.status_code == 404
    assert response.json["error"]["code"] == "not_found"
    assert response.headers["Cache-Control"] == "no-store"


def test_update_topic_persists_all_editable_fields(client, test_app):
    user_id = create_user(test_app)
    topic_id = create_topic(test_app, user_id)
    sign_in(client, user_id)

    response = client.patch(
        f"/api/topics/{topic_id}",
        json=topic_payload(
            title="  Updated topic  ",
            description="  Updated description  ",
            color="#aAbBcC",
            user_id=user_id + 10,
            note_count=100,
        ),
    )

    assert response.status_code == 200
    assert response.headers["Cache-Control"] == "no-store"
    assert response.json["topic"]["title"] == "Updated topic"
    assert response.json["topic"]["description"] == "Updated description"
    assert response.json["topic"]["color"] == "#aAbBcC"
    assert response.json["topic"]["note_count"] == 0
    with test_app.app_context():
        topic = db.session.get(Topic, topic_id)
        assert topic.title == "Updated topic"
        assert topic.description == "Updated description"
        assert topic.color == "#aAbBcC"


def test_update_topic_returns_404_for_missing_or_foreign_topics(
    client, test_app
):
    user_id = create_user(test_app)
    other_user_id = create_user(
        test_app, username="other", email="other@example.com"
    )
    foreign_topic_id = create_topic(test_app, other_user_id)
    sign_in(client, user_id)

    for topic_id in (foreign_topic_id, 999999):
        response = client.patch(
            f"/api/topics/{topic_id}",
            json=topic_payload(title="Must not change"),
        )
        assert response.status_code == 404
        assert response.json["error"]["code"] == "not_found"
    with test_app.app_context():
        assert db.session.get(Topic, foreign_topic_id).title == "Databases"


@pytest.mark.parametrize(
    ("payload", "expected_message"),
    [
        (topic_payload(title=" "), "Title is required."),
        (topic_payload(description=" "), "Description is required."),
        (topic_payload(color="blue"), "Color must be a six-digit hex color."),
    ],
)
def test_update_topic_rejects_invalid_fields_without_changing_topic(
    client, test_app, payload, expected_message
):
    user_id = create_user(test_app)
    topic_id = create_topic(test_app, user_id)
    sign_in(client, user_id)

    response = client.patch(f"/api/topics/{topic_id}", json=payload)

    assert response.status_code == 400
    assert response.json["error"]["code"] == "validation_error"
    assert response.json["error"]["message"] == expected_message
    with test_app.app_context():
        topic = db.session.get(Topic, topic_id)
        assert topic.title == "Databases"
        assert topic.description == "Database concepts"
        assert topic.color == "#087f65"


@pytest.mark.parametrize(
    ("reference_type", "model"),
    [
        ("note", Note),
        ("flashcard", Flashcard),
        ("progress", Progress),
        ("quiz_attempt", QuizAttempt),
    ],
)
def test_delete_topic_refuses_any_direct_study_reference(
    client, test_app, reference_type, model
):
    user_id = create_user(test_app)
    topic_id = create_topic(test_app, user_id)
    with test_app.app_context():
        if reference_type == "note":
            linked_record = Note(
                user_id=user_id,
                topic_id=topic_id,
                title="Reference",
                content="Text",
            )
        elif reference_type == "flashcard":
            note = Note(
                user_id=user_id,
                title="Flashcard source",
                content="Text",
            )
            db.session.add(note)
            db.session.flush()
            linked_record = Flashcard(
                user_id=user_id,
                topic_id=topic_id,
                note_id=note.id,
                question="Question",
                answer="Answer",
            )
        elif reference_type == "progress":
            linked_record = Progress(user_id=user_id, topic_id=topic_id)
        else:
            note = Note(
                user_id=user_id,
                title="Quiz source",
                content="Text",
            )
            db.session.add(note)
            db.session.flush()
            linked_record = QuizAttempt(
                user_id=user_id,
                topic_id=topic_id,
                note_id=note.id,
            )
        db.session.add(linked_record)
        db.session.commit()
        linked_id = linked_record.id
    sign_in(client, user_id)

    response = client.delete(f"/api/topics/{topic_id}")

    assert response.status_code == 409
    assert response.json["error"] == {
        "code": "topic_not_empty",
        "message": "Move this topic's notes and other study data before deleting it.",
    }
    assert response.headers["Cache-Control"] == "no-store"
    with test_app.app_context():
        assert db.session.get(Topic, topic_id) is not None
        assert db.session.get(model, linked_id) is not None


def test_delete_empty_topic_returns_204_and_removes_only_that_topic(
    client, test_app
):
    user_id = create_user(test_app)
    topic_id = create_topic(test_app, user_id)
    other_topic_id = create_topic(test_app, user_id, "Another")
    sign_in(client, user_id)

    response = client.delete(f"/api/topics/{topic_id}")

    assert response.status_code == 204
    assert response.data == b""
    assert response.headers["Cache-Control"] == "no-store"
    with test_app.app_context():
        assert db.session.get(Topic, topic_id) is None
        assert db.session.get(Topic, other_topic_id) is not None


def test_delete_topic_returns_404_for_missing_or_foreign_topics(
    client, test_app
):
    user_id = create_user(test_app)
    other_user_id = create_user(
        test_app, username="other", email="other@example.com"
    )
    foreign_topic_id = create_topic(test_app, other_user_id)
    sign_in(client, user_id)

    for topic_id in (foreign_topic_id, 999999):
        response = client.delete(f"/api/topics/{topic_id}")
        assert response.status_code == 404
        assert response.json["error"]["code"] == "not_found"
    with test_app.app_context():
        assert db.session.get(Topic, foreign_topic_id) is not None


def test_topic_mutations_enforce_csrf(client, test_app):
    user_id = create_user(test_app)
    topic_id = create_topic(test_app, user_id)
    sign_in(client, user_id)
    test_app.config["WTF_CSRF_ENABLED"] = True

    missing_tokens = (
        client.post("/api/topics", json=topic_payload()),
        client.patch(
            f"/api/topics/{topic_id}",
            json=topic_payload(title="Must be blocked"),
        ),
        client.delete(f"/api/topics/{topic_id}"),
    )
    token_response = client.get("/api/auth/csrf")
    headers = {"X-CSRFToken": token_response.json["csrf_token"]}
    created = client.post("/api/topics", json=topic_payload(), headers=headers)
    updated = client.patch(
        f"/api/topics/{topic_id}",
        json=topic_payload(title="Changed"),
        headers=headers,
    )
    deleted = client.delete(f"/api/topics/{created.json['topic']['id']}", headers=headers)

    for response in missing_tokens:
        assert response.status_code == 400
        assert response.json["error"]["code"] == "csrf_failed"
        assert response.headers["Cache-Control"] == "no-store"
    assert created.status_code == 201
    assert updated.status_code == 200
    assert deleted.status_code == 204


def test_unexpected_topic_service_errors_are_logged_and_sanitized(
    client, test_app, monkeypatch
):
    user_id = create_user(test_app)
    sign_in(client, user_id)

    def fail_to_list_topics(requesting_user_id):
        assert requesting_user_id == user_id
        raise RuntimeError("database details must not be exposed")

    monkeypatch.setattr(
        "backend.services.topic_service.list_topics",
        fail_to_list_topics,
    )
    response = client.get("/api/topics")

    assert response.status_code == 500
    assert response.json["error"] == {
        "code": "internal_error",
        "message": "Unable to load topics.",
    }
    assert "database details" not in response.get_data(as_text=True)
    assert response.headers["Cache-Control"] == "no-store"
