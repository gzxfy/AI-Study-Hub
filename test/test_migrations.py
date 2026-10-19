"""Exercise real Alembic upgrades without db.create_all() or a user's database."""
from datetime import datetime

import pytest
import sqlalchemy as sa

from backend import create_app, db
from backend.models.models import FlashcardProgress, StudyPlan
from backend.services import assistant_service


HEAD = "d8a17c09e452"


@pytest.fixture
def migrated_app(tmp_path):
    app = create_app({
        "TESTING": True,
        "SECRET_KEY": "migration-test-only",
        "SQLALCHEMY_DATABASE_URI": f"sqlite:///{(tmp_path / 'fresh.db').as_posix()}",
        "WTF_CSRF_ENABLED": True,
    })
    yield app
    with app.app_context():
        db.session.remove()
        db.engine.dispose()


def upgrade(app, revision="head"):
    result = app.test_cli_runner().invoke(args=["db", "upgrade", revision])
    assert result.exit_code == 0, f"{result.output}\n{result.exception!r}"


def post(client, path, payload):
    # Login rotates the session, so obtain a fresh token for each mutation.
    token = client.get("/api/auth/csrf").json["csrf_token"]
    return client.post(path, json=payload, headers={"X-CSRFToken": token})


def test_empty_database_upgrade_matches_model_columns(migrated_app):
    upgrade(migrated_app)
    with migrated_app.app_context():
        inspector = sa.inspect(db.engine)
        assert set(inspector.get_table_names()) == set(db.metadata.tables) | {"alembic_version"}
        for table in db.metadata.sorted_tables:
            actual = {column["name"]: column for column in inspector.get_columns(table.name)}
            assert set(actual) == set(table.columns.keys()), table.name
            for column in table.columns:
                assert actual[column.name]["nullable"] == column.nullable, f"{table.name}.{column.name}"
        progress_columns = {column["name"]: column for column in inspector.get_columns("flashcard_progress")}
        assert isinstance(progress_columns["progress"]["type"], sa.Float)
        assert db.session.execute(sa.text("SELECT version_num FROM alembic_version")).scalar_one() == HEAD


def test_migrated_database_supports_signed_in_study_flow(migrated_app, monkeypatch):
    upgrade(migrated_app)
    client = migrated_app.test_client()
    password = "MigrationTest1!"
    response = post(client, "/api/auth/register", {
        "username": "new-student", "email": "new@example.com",
        "password": password, "confirm_password": password,
    })
    assert response.status_code == 201, response.json
    assert post(client, "/api/auth/login", {"email": "new@example.com", "password": password}).status_code == 200
    response = post(client, "/api/topics", {"title": "Algorithms", "description": "Algorithm revision", "color": "#168A72"})
    assert response.status_code == 201, response.json
    topic_id = response.json["topic"]["id"]
    response = post(client, "/api/notes", {"title": "Binary search", "content": "Halve a sorted search space.", "topic_id": topic_id})
    assert response.status_code == 201, response.json
    note_id = response.json["note"]["id"]
    response = post(client, "/api/flashcards", {
        "question": "What is its complexity?", "answer": "O(log n)",
        "note_id": note_id, "topic_id": topic_id, "difficulty": "easy",
    })
    assert response.status_code == 201, response.json
    card_id = response.json["flashcard"]["id"]
    response = client.get(f"/study_mode/start?note_id={note_id}")
    assert response.status_code == 200
    assert [card["id"] for card in response.json] == [card_id]
    assert post(client, "/study_mode/review", {"flashcard_id": card_id, "marked_correctly": True}).status_code == 200
    monkeypatch.setattr(assistant_service, "ask_ai", lambda *args: "Binary search halves the search space.")
    response = post(client, f"/api/notes/{note_id}/messages", {"message": "Explain it", "request_id": "fresh-test"})
    assert response.status_code == 200, response.json
    assert [message["role"] for message in response.json["messages"]] == ["user", "assistant"]

    # Running setup again must not reset saved material or conversation history.
    upgrade(migrated_app)
    assert client.get(f"/api/notes/{note_id}").status_code == 200
    assert len(client.get(f"/api/notes/{note_id}/conversation").json["messages"]) == 2
    with migrated_app.app_context():
        assert FlashcardProgress.query.one().times_seen == 1
        plan = StudyPlan(user_id=1, title="Revision", start_date=datetime(2026, 1, 1), end_date=datetime(2026, 1, 2))
        db.session.add(plan)
        db.session.commit()
        assert plan.completed is False


def test_upgrade_preserves_legacy_reviews_and_backfills_plan_flag(migrated_app):
    upgrade(migrated_app, "1f4296c2362e")
    with migrated_app.app_context():
        db.session.execute(sa.text("INSERT INTO user (id, username, email, password_hash) VALUES (1, 'existing', 'old@example.com', 'test-only')"))
        db.session.execute(sa.text("INSERT INTO notes (id, user_id, title, content) VALUES (1, 1, 'Saved note', 'Keep this content')"))
        db.session.execute(sa.text("INSERT INTO flashcards (id, user_id, note_id, question, answer) VALUES (1, 1, 1, 'Question', 'Answer')"))
        db.session.execute(sa.text("INSERT INTO flashcard_progress (user_id, flashcard_id, times_seen, times_correct, streak, progress) VALUES (1, 1, 3, 1, 1, 1)"))
        db.session.execute(sa.text("INSERT INTO study_plans (user_id, title, start_date, end_date) VALUES (1, 'Existing plan', '2026-01-01', '2026-01-02')"))
        db.session.commit()
    upgrade(migrated_app)
    with migrated_app.app_context():
        progress = FlashcardProgress.query.one()
        assert (progress.times_seen, progress.times_correct, progress.progress) == (3, 1, 1.0)
        assert StudyPlan.query.one().completed is False


def test_upgrade_accepts_model_created_completed_column(migrated_app):
    upgrade(migrated_app, "c912d45b810e")
    with migrated_app.app_context():
        db.session.execute(sa.text("ALTER TABLE study_plans ADD COLUMN completed BOOLEAN NOT NULL DEFAULT 0"))
        db.session.commit()
    upgrade(migrated_app)
