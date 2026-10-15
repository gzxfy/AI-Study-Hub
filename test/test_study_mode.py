import pytest

from backend import db
from backend.models.models import (
    Flashcard,
    FlashcardProgress,
    Note,
    StudyEvent,
    User,
)
from backend.services import study_mode_service


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


def create_note(test_app, user_id, title="Study note"):
    with test_app.app_context():
        note = Note(
            user_id=user_id,
            title=title,
            content="Notes for a study session.",
        )
        db.session.add(note)
        db.session.commit()
        return note.id


def create_flashcard(
    test_app,
    user_id,
    note_id,
    question="Question",
    answer="Answer",
    difficulty="easy",
):
    with test_app.app_context():
        flashcard = Flashcard(
            user_id=user_id,
            note_id=note_id,
            question=question,
            answer=answer,
            difficulty=difficulty,
        )
        db.session.add(flashcard)
        db.session.commit()
        return flashcard.id


def create_progress(
    test_app, user_id, flashcard_id, times_seen, times_correct, streak=0
):
    with test_app.app_context():
        progress = FlashcardProgress(
            user_id=user_id,
            flashcard_id=flashcard_id,
            times_seen=times_seen,
            times_correct=times_correct,
            streak=streak,
        )
        db.session.add(progress)
        db.session.commit()


def test_study_routes_require_a_valid_session(client, test_app):
    anonymous_responses = (
        client.get("/study_mode/start?note_id=1"),
        client.post(
            "/study_mode/review",
            json={"flashcard_id": 1, "marked_correctly": True},
        ),
        client.post("/study_mode/end", json={"reviewed_results": []}),
    )
    for response in anonymous_responses:
        assert response.status_code == 401
        assert response.json["error"]["code"] == "unauthenticated"
        assert response.headers["Cache-Control"] == "no-store"

    sign_in(client, 999)
    stale_session_responses = (
        client.get("/study_mode/start?note_id=1"),
        client.post("/study_mode/review", json={}),
        client.post("/study_mode/end", json={}),
    )
    for response in stale_session_responses:
        assert response.status_code == 401
        assert response.json["error"]["code"] == "unauthenticated"


def test_start_study_returns_only_matching_owned_cards(client, test_app):
    user_id = create_user(test_app)
    other_user_id = create_user(
        test_app, username="other", email="other@example.com"
    )
    note_id = create_note(test_app, user_id)
    another_note_id = create_note(test_app, user_id, title="Other note")
    easy_first_id = create_flashcard(
        test_app, user_id, note_id, question="Easy first", difficulty="easy"
    )
    easy_second_id = create_flashcard(
        test_app, user_id, note_id, question="Easy second", difficulty="easy"
    )
    create_flashcard(
        test_app, user_id, note_id, question="Hard card", difficulty="hard"
    )
    create_flashcard(
        test_app, user_id, another_note_id, question="Other note card"
    )
    create_flashcard(
        test_app, other_user_id, note_id, question="Private card"
    )
    sign_in(client, user_id)

    response = client.get(
        f"/study_mode/start?note_id={note_id}&difficulty=easy&card_count=2"
    )

    assert response.status_code == 200
    assert response.headers["Cache-Control"] == "no-store"
    assert {card["id"] for card in response.json} == {
        easy_first_id,
        easy_second_id,
    }
    assert all(card["difficulty"] == "easy" for card in response.json)
    assert all("answer" in card and "question" in card for card in response.json)


def test_start_study_with_foreign_note_returns_no_cards(client, test_app):
    user_id = create_user(test_app)
    other_user_id = create_user(
        test_app, username="other", email="other@example.com"
    )
    other_note_id = create_note(test_app, other_user_id)
    create_flashcard(test_app, other_user_id, other_note_id)
    sign_in(client, user_id)

    response = client.get(f"/study_mode/start?note_id={other_note_id}")

    assert response.status_code == 200
    assert response.json == []


@pytest.mark.parametrize(
    ("query", "expected_code"),
    [
        ("", "invalid_parameters"),
        ("note_id=0", "invalid_parameters"),
        ("note_id=1&card_count=0", "invalid_parameters"),
        ("note_id=1&card_count=invalid", "invalid_parameters"),
        ("note_id=1&difficulty=impossible", "invalid_parameters"),
        ("note_id=1&priority=yes", "invalid_priority"),
    ],
)
def test_start_study_rejects_invalid_query_parameters(
    client, test_app, query, expected_code
):
    user_id = create_user(test_app)
    sign_in(client, user_id)

    response = client.get(f"/study_mode/start?{query}")

    assert response.status_code == 400
    assert response.json["error"]["code"] == expected_code
    assert response.headers["Cache-Control"] == "no-store"


def test_priority_study_ranks_all_matching_cards_before_limit(test_app):
    user_id = create_user(test_app)
    note_id = create_note(test_app, user_id)
    unseen_id = create_flashcard(test_app, user_id, note_id, question="Unseen")
    no_correct_id = create_flashcard(
        test_app, user_id, note_id, question="No correct reviews"
    )
    low_accuracy_id = create_flashcard(
        test_app, user_id, note_id, question="Low accuracy"
    )
    mastered_id = create_flashcard(
        test_app, user_id, note_id, question="Mastered"
    )
    create_progress(test_app, user_id, no_correct_id, 4, 0)
    create_progress(test_app, user_id, low_accuracy_id, 3, 1)
    create_progress(test_app, user_id, mastered_id, 5, 5)

    with test_app.app_context():
        cards = study_mode_service.start_study_mode(
            user_id=user_id,
            note_id=note_id,
            card_count=2,
            priority=True,
        )

    assert [card.id for card in cards] == [unseen_id, no_correct_id]
    assert low_accuracy_id not in [card.id for card in cards]
    assert mastered_id not in [card.id for card in cards]


def test_service_start_shuffles_without_priority(test_app, monkeypatch):
    user_id = create_user(test_app)
    note_id = create_note(test_app, user_id)
    card_ids = [
        create_flashcard(test_app, user_id, note_id, question=f"Question {index}")
        for index in range(3)
    ]

    def reverse_cards(cards):
        cards.reverse()

    monkeypatch.setattr(study_mode_service.random, "shuffle", reverse_cards)
    with test_app.app_context():
        cards = study_mode_service.start_study_mode(user_id, note_id)

    assert [card.id for card in cards] == list(reversed(card_ids))


def test_service_rejects_invalid_filters(test_app):
    user_id = create_user(test_app)
    note_id = create_note(test_app, user_id)

    with test_app.app_context(), pytest.raises(ValueError):
        study_mode_service.start_study_mode(
            user_id, note_id, card_count=True
        )
    with test_app.app_context(), pytest.raises(ValueError):
        study_mode_service.start_study_mode(
            user_id, note_id, difficulty="unknown"
        )
    with test_app.app_context(), pytest.raises(ValueError):
        study_mode_service.start_study_mode(
            user_id, note_id, priority="true"
        )


def test_review_route_persists_event_and_progress(client, test_app):
    user_id = create_user(test_app)
    note_id = create_note(test_app, user_id)
    flashcard_id = create_flashcard(test_app, user_id, note_id)
    sign_in(client, user_id)

    first_response = client.post(
        "/study_mode/review",
        json={"flashcard_id": flashcard_id, "marked_correctly": True},
    )
    second_response = client.post(
        "/study_mode/review",
        json={"flashcard_id": flashcard_id, "marked_correctly": False},
    )

    assert first_response.status_code == 200
    assert first_response.headers["Cache-Control"] == "no-store"
    assert first_response.json == {
        "flashcard_id": flashcard_id,
        "times_seen": 1,
        "times_correct": 1,
        "streak": 1,
        "progress": 1.0,
    }
    assert second_response.status_code == 200
    assert second_response.json["times_seen"] == 2
    assert second_response.json["times_correct"] == 1
    assert second_response.json["streak"] == 0
    assert second_response.json["progress"] == 0.5

    with test_app.app_context():
        progress = FlashcardProgress.query.filter_by(
            user_id=user_id,
            flashcard_id=flashcard_id,
        ).one()
        events = StudyEvent.query.filter_by(
            user_id=user_id,
            flashcard_id=flashcard_id,
        ).order_by(StudyEvent.id).all()
        assert (progress.times_seen, progress.times_correct, progress.streak) == (
            2,
            1,
            0,
        )
        assert [event.is_correct for event in events] == [True, False]
        assert all(event.source == "study_mode" for event in events)


@pytest.mark.parametrize(
    "payload",
    [
        None,
        {"flashcard_id": True, "marked_correctly": True},
        {"flashcard_id": 1, "marked_correctly": "true"},
        {"flashcard_id": 1},
    ],
)
def test_review_rejects_invalid_input_without_writing(client, test_app, payload):
    user_id = create_user(test_app)
    note_id = create_note(test_app, user_id)
    create_flashcard(test_app, user_id, note_id)
    sign_in(client, user_id)

    response = client.post("/study_mode/review", json=payload)

    assert response.status_code == 400
    assert response.json["error"]["code"] in {"invalid_json", "invalid_fields"}
    with test_app.app_context():
        assert FlashcardProgress.query.count() == 0
        assert StudyEvent.query.count() == 0


def test_review_hides_missing_and_foreign_cards(client, test_app):
    user_id = create_user(test_app)
    other_user_id = create_user(
        test_app, username="other", email="other@example.com"
    )
    other_note_id = create_note(test_app, other_user_id)
    foreign_card_id = create_flashcard(test_app, other_user_id, other_note_id)
    sign_in(client, user_id)

    responses = (
        client.post(
            "/study_mode/review",
            json={"flashcard_id": foreign_card_id, "marked_correctly": True},
        ),
        client.post(
            "/study_mode/review",
            json={"flashcard_id": 999999, "marked_correctly": True},
        ),
    )

    for response in responses:
        assert response.status_code == 404
        assert response.json["error"]["code"] == "not_found"
    with test_app.app_context():
        assert FlashcardProgress.query.count() == 0
        assert StudyEvent.query.count() == 0


def test_end_study_returns_summary_of_confirmed_results(client, test_app):
    user_id = create_user(test_app)
    sign_in(client, user_id)

    response = client.post(
        "/study_mode/end",
        json={
            "reviewed_results": [
                {"flashcard_id": 1, "correct": True},
                {"flashcard_id": 2, "correct": False},
                {"flashcard_id": 3, "correct": True},
            ]
        },
    )

    assert response.status_code == 200
    assert response.headers["Cache-Control"] == "no-store"
    assert response.json == {
        "user_id": user_id,
        "reviewed_count": 3,
        "correct_count": 2,
        "accuracy": 66.67,
    }


def test_end_study_returns_zero_summary_when_no_cards_were_reviewed(
    client, test_app
):
    user_id = create_user(test_app)
    sign_in(client, user_id)

    response = client.post("/study_mode/end", json={"reviewed_results": []})

    assert response.status_code == 200
    assert response.json == {
        "user_id": user_id,
        "reviewed_count": 0,
        "correct_count": 0,
        "accuracy": 0,
    }


@pytest.mark.parametrize(
    "reviewed_results",
    [
        None,
        "not a list",
        [None],
        [{"flashcard_id": 1, "correct": 1}],
        [{"flashcard_id": True, "correct": True}],
        [{"flashcard_id": 1}],
    ],
)
def test_end_study_rejects_invalid_results(client, test_app, reviewed_results):
    user_id = create_user(test_app)
    sign_in(client, user_id)

    response = client.post(
        "/study_mode/end",
        json={"reviewed_results": reviewed_results},
    )

    assert response.status_code == 400
    assert response.json["error"]["code"] == "invalid_fields"


def test_study_mutations_require_csrf_token(client, test_app):
    user_id = create_user(test_app)
    note_id = create_note(test_app, user_id)
    flashcard_id = create_flashcard(test_app, user_id, note_id)
    sign_in(client, user_id)
    test_app.config["WTF_CSRF_ENABLED"] = True

    review_response = client.post(
        "/study_mode/review",
        json={"flashcard_id": flashcard_id, "marked_correctly": True},
    )
    end_response = client.post(
        "/study_mode/end",
        json={"reviewed_results": []},
    )

    assert review_response.status_code == 400
    assert end_response.status_code == 400
    assert review_response.json["error"]["code"] == "csrf_failed"
    assert end_response.json["error"]["code"] == "csrf_failed"
    assert review_response.headers["Cache-Control"] == "no-store"
    assert end_response.headers["Cache-Control"] == "no-store"
    test_app.config["WTF_CSRF_ENABLED"] = False