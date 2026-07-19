# CHANGED: Fixed import - only import db from app, not from models
from app import db
from app.models.models import User, Note, Flashcard


def _create_test_user_with_flashcards(test_app, username="testuser", email="test@example.com"):
    """Helper to create a user, note, and 3 flashcards for reuse across tests."""
    with test_app.app_context():
        user = User(username=username, email=email, password_hash="hashed")
        db.session.add(user)
        db.session.flush()
        user_id = user.id

        note = Note(user_id=user_id, title="Test Note", content="Content")
        db.session.add(note)
        db.session.flush()
        note_id = note.id

        flashcard_ids = []
        for q, a in [("Q1", "A1"), ("Q2", "A2"), ("Q3", "A3")]:
            fc = Flashcard(
                user_id=user_id,
                note_id=note_id,
                question=q,
                answer=a,
                difficulty="easy" if a in ["A1", "A2"] else "hard",
            )
            db.session.add(fc)
            db.session.flush()
            flashcard_ids.append({"id": fc.id, "question": q, "answer": a})

        db.session.commit()
        return user_id, note_id, flashcard_ids


def test_start_quiz_returns_questions(client, test_app):
    """Test that POST /quiz/start creates a quiz attempt and returns ordered questions."""
    user_id, note_id, flashcards = _create_test_user_with_flashcards(test_app, username="user1", email="user1@example.com")

    with client.session_transaction() as session:
        session['user_id'] = user_id
        session['username'] = "user1"

    response = client.post(
        "/quiz/start",
        json={
            "note_id": note_id,
            "question_count": 2,
        }
    )
    data = response.get_json()

    assert response.status_code == 200
    assert "quiz_attempt_id" in data
    assert "questions" in data
    # CHANGED: Added assertions for status and question_index returned by route
    assert "status" in data
    assert data["status"] == "in_progress"
    assert data["question_index"] == 0
    assert len(data['questions']) == 2
    # CHANGED: Verify answers are NOT included in start response (security)
    for q in data["questions"]:
        assert "id" in q
        assert "question" in q
        assert "difficulty" in q
        assert "answer" not in q


def test_start_quiz_validates_note_id(client, test_app):
    """Test that POST /quiz/start returns 400 if note_id is missing or invalid."""
    user_id, note_id, _ = _create_test_user_with_flashcards(test_app)

    with client.session_transaction() as session:
        session["user_id"] = user_id
        session["username"] = "testuser"

    response = client.post(
        "/quiz/start",
        json={
            "difficulty": "easy", 
            "question_count": 2
        }
    )
    assert response.status_code == 400
    assert "note_id is required and must be a positive integer" in response.get_json().get("error", "")


def test_get_current_quiz_question(client, test_app):
    """Test that GET /quiz/current returns the current question based on question_index."""
    user_id, note_id, _ = _create_test_user_with_flashcards(test_app, username="user2", email="user2@example.com")

    with client.session_transaction() as session:
        session['user_id'] = user_id
        session['username'] = "user2"

    # Start quiz first
    start_response = client.post(
        "/quiz/start",
        json={
            "note_id": note_id,
            "difficulty": "easy",
            "question_count": 2,
        }
    )

    start_data = start_response.get_json()
    quiz_attempt_id = start_data["quiz_attempt_id"]

    response = client.get(f"/quiz/current?quiz_attempt_id={quiz_attempt_id}")
    data = response.get_json()

    assert response.status_code == 200
    assert "quiz_attempt_id" in data
    assert data["quiz_attempt_id"] == quiz_attempt_id
    assert "status" in data
    assert data["status"] == "in_progress"
    assert "question_index" in data
    assert data["question_index"] == 0

    # CHANGED: Fixed - response has single "question" object, NOT "questions" array
    assert "question" in data
    question = data["question"]
    assert "id" in question
    assert "question" in question
    assert "difficulty" in question
    # CHANGED: Verify answer not leaked in GET current
    assert "answer" not in question


def test_submit_quiz_answer_marks_correct(client, test_app):
    """Test that POST /quiz/submit_answer records correct answer and updates score."""
    user_id, note_id, flashcards = _create_test_user_with_flashcards(test_app, username="user3", email="user3@example.com")

    with client.session_transaction() as session:
        session["user_id"] = user_id
        session["username"] = "user3"

    # Start quiz
    start_response = client.post(
        "/quiz/start",
        json={"note_id": note_id, "question_count": 2},
    )
    start_data = start_response.get_json()
    quiz_attempt_id = start_data["quiz_attempt_id"]

    # Use the served question order from /quiz/start (questions are shuffled).
    first_question_id = start_data["questions"][0]["id"]
    first_card = next(fc for fc in flashcards if fc["id"] == first_question_id)

    # Submit correct answer
    response = client.post(
        "/quiz/submit_answer",
        json={
            "quiz_attempt_id": quiz_attempt_id,
            "flashcard_id": first_card["id"],
            "user_answer": first_card["answer"],
            "time_taken": 5.0,
        },
    )
    # CHANGED: New test for submit_answer endpoint
    data = response.get_json()

    assert response.status_code == 200
    assert data["is_correct"] is True
    assert data["correct_answer"] == first_card["answer"]
    # CHANGED: 1 correct out of 2 total = 50%
    assert data["score"] == 50.0
    # CHANGED: question_index incremented after first answer
    assert data["question_index"] == 1
    assert data["status"] == "in_progress"
    # CHANGED: next_question is returned as object or None (safe to access)
    assert "next_question" in data
    assert data["next_question"] is not None


def test_submit_quiz_answer_marks_incorrect(client, test_app):
    """Test that POST /quiz/submit_answer records incorrect answer."""
    user_id, note_id, flashcards = _create_test_user_with_flashcards(test_app, username="user4", email="user4@example.com")

    with client.session_transaction() as session:
        session["user_id"] = user_id
        session["username"] = "user4"

    # Start quiz
    start_response = client.post(
        "/quiz/start",
        json={"note_id": note_id, "question_count": 2},
    )
    start_data = start_response.get_json()
    quiz_attempt_id = start_data["quiz_attempt_id"]

    first_question_id = start_data["questions"][0]["id"]
    first_card = next(fc for fc in flashcards if fc["id"] == first_question_id)

    # Submit incorrect answer
    response = client.post(
        "/quiz/submit_answer",
        json={
            "quiz_attempt_id": quiz_attempt_id,
            "flashcard_id": first_card["id"],
            "user_answer": "wrong answer",
            "time_taken": 3.0,
        },
    )
    data = response.get_json()

    assert response.status_code == 200
    # CHANGED: New test - verify incorrect answer is tracked
    assert data["is_correct"] is False
    assert data["correct_answer"] == first_card["answer"]
    # CHANGED: 0 correct out of 2 = 0%
    assert data["score"] == 0.0
    assert data["question_index"] == 1


def test_finish_quiz_returns_summary(client, test_app):
    """Test that POST /quiz/finish marks quiz complete and returns final summary."""
    user_id, note_id, flashcards = _create_test_user_with_flashcards(test_app, username="user5", email="user5@example.com")

    with client.session_transaction() as session:
        session["user_id"] = user_id
        session["username"] = "user5"

    # Start quiz
    start_response = client.post(
        "/quiz/start",
        json={"note_id": note_id, "question_count": 2},
    )
    start_data = start_response.get_json()
    quiz_attempt_id = start_data["quiz_attempt_id"]

    ordered_cards = [
        next(fc for fc in flashcards if fc["id"] == q["id"])
        for q in start_data["questions"]
    ]

    # Submit both answers
    for fc in ordered_cards:
        client.post(
            "/quiz/submit_answer",
            json={
                "quiz_attempt_id": quiz_attempt_id,
                "flashcard_id": fc["id"],
                "user_answer": fc["answer"],
                "time_taken": 2.0,
            },
        )

    # Finish quiz
    # CHANGED: New test for finish endpoint
    response = client.post(
        "/quiz/finish",
        json={"quiz_attempt_id": quiz_attempt_id},
    )
    data = response.get_json()

    assert response.status_code == 200
    # CHANGED: Service returns summary dict directly, NOT nested under "summary" key
    assert "quiz_attempt_id" in data
    assert "status" in data
    assert data["status"] == "completed"
    assert "total_questions" in data
    assert data["total_questions"] == 2
    assert "total_answered" in data
    assert data["total_answered"] == 2
    assert "total_correct" in data
    assert data["total_correct"] == 2
    assert "score" in data
    assert data["score"] == 100.0


def test_review_quiz_question_without_ai(client, test_app):
    """Test that GET /quiz/review/question returns review payload without AI."""
    user_id, note_id, flashcards = _create_test_user_with_flashcards(test_app, username="user6", email="user6@example.com")

    with client.session_transaction() as session:
        session["user_id"] = user_id
        session["username"] = "user6"

    # Start and submit answer
    start_response = client.post(
        "/quiz/start",
        json={"note_id": note_id, "question_count": 2},
    )
    quiz_attempt_id = start_response.get_json()["quiz_attempt_id"]

    fc = flashcards[0]
    client.post(
        "/quiz/submit_answer",
        json={
            "quiz_attempt_id": quiz_attempt_id,
            "flashcard_id": fc["id"],
            "user_answer": "wrong",
            "time_taken": 2.0,
        },
    )

    # Review question
    # CHANGED: New test for review/question endpoint
    response = client.get(
        f"/quiz/review/question?quiz_attempt_id={quiz_attempt_id}&flashcard_id={fc['id']}&ask_ai=false"
    )
    data = response.get_json()

    assert response.status_code == 200
    # CHANGED: Service returns full review dict, NOT nested under "feedback" key
    assert "quiz_attempt_id" in data
    assert "flashcard_id" in data
    assert "question" in data
    assert data["question"] == fc["question"]
    assert "user_answer" in data
    assert data["user_answer"] == "wrong"
    assert "correct_answer" in data
    assert data["correct_answer"] == fc["answer"]
    assert "is_correct" in data
    assert data["is_correct"] is False
    assert "time_taken" in data
    assert "ai_explanation" in data
    # CHANGED: AI explanation is None when ask_ai=false
    assert data["ai_explanation"] is None


def test_review_quiz_summary(client, test_app):
    """Test that GET /quiz/review/summary returns full quiz report."""
    user_id, note_id, flashcards = _create_test_user_with_flashcards(test_app, username="user7", email="user7@example.com")

    with client.session_transaction() as session:
        session["user_id"] = user_id
        session["username"] = "user7"

    # Start and submit all answers
    start_response = client.post(
        "/quiz/start",
        json={"note_id": note_id, "question_count": 2},
    )
    start_data = start_response.get_json()
    quiz_attempt_id = start_data["quiz_attempt_id"]

    # Submit answers in the exact order provided by the quiz attempt.
    ordered_cards = [
        next(fc for fc in flashcards if fc["id"] == q["id"])
        for q in start_data["questions"]
    ]

    for i, fc in enumerate(ordered_cards):
        is_correct = (i == 0)  # First is correct, second is incorrect
        client.post(
            "/quiz/submit_answer",
            json={
                "quiz_attempt_id": quiz_attempt_id,
                "flashcard_id": fc["id"],
                "user_answer": fc["answer"] if is_correct else "wrong",
                "time_taken": 2.0,
            },
        )

    # Get summary
    response = client.get(
        f"/quiz/review/summary?quiz_attempt_id={quiz_attempt_id}&ask_ai=false"
    )
    data = response.get_json()

    assert response.status_code == 200
    # CHANGED: Service returns summary dict with top-level fields, NOT nested under "summary"
    assert "quiz_attempt_id" in data
    assert "status" in data
    assert "total_questions" in data
    assert data["total_questions"] == 2
    assert "total_answered" in data
    assert "total_correct" in data
    assert data["total_correct"] == 1
    assert "score" in data
    assert data["score"] == 50.0
    assert "items" in data
    assert len(data["items"]) == 2
    # CHANGED: Each item is a review payload with ai_explanation field
    for item in data["items"]:
        assert "flashcard_id" in item
        assert "question" in item
        assert "user_answer" in item
        assert "correct_answer" in item
        assert "is_correct" in item
        assert "time_taken" in item
        assert "ai_explanation" in item