import pytest

from backend import db
from backend.models import Quiz, QuizAttempt, QuizQuestion, QuizQuestionAttempt, User


@pytest.mark.parametrize("app_fixture", ["test_app", "postgres_app"])
def test_saved_quiz_persists_score_and_enforces_attempt_rules(request, app_fixture):
    app = request.getfixturevalue(app_fixture)
    with app.app_context():
        student = User(username="student", email="student@example.com", password_hash="test-only")
        other_student = User(username="other", email="other@example.com", password_hash="test-only")
        quiz = Quiz(title="General Knowledge")
        db.session.add_all([student, other_student, quiz])
        db.session.flush()
        first = QuizQuestion(quiz_id=quiz.id, question_text="Capital of Japan?", correct_answer="Tokyo")
        second = QuizQuestion(quiz_id=quiz.id, question_text="Sides of a hexagon?", correct_answer="6")
        db.session.add_all([first, second])
        db.session.commit()
        student_id, other_id, quiz_id = student.id, other_student.id, quiz.id
        first_id, second_id = first.id, second.id

    client = app.test_client()
    assert client.get("/api/quizzes").status_code == 401
    with client.session_transaction() as session:
        session["user_id"] = student_id

    assert client.get("/api/quizzes").json["quizzes"][0]["id"] == quiz_id
    start_path = f"/api/quizzes/{quiz_id}/attempts"
    started = client.post(start_path)
    assert started.status_code == 201, started.json
    assert started.json["question"] == {"id": first_id, "question": "Capital of Japan?"}
    attempt_id = started.json["quiz_attempt_id"]
    resumed = client.post(start_path)
    assert resumed.status_code == 200
    assert resumed.json == started.json

    answer_path = f"/api/quiz-attempts/{attempt_id}/answers"
    other_client = app.test_client()
    with other_client.session_transaction() as session:
        session["user_id"] = other_id
    assert other_client.post(answer_path, json={"question_id": first_id, "answer": "Tokyo"}).status_code == 404
    assert client.post(answer_path, json={"question_id": second_id, "answer": "6"}).status_code == 409

    first_answer = {"question_id": first_id, "answer": " tokyo "}
    graded = client.post(answer_path, json=first_answer)
    assert graded.status_code == 200, graded.json
    assert graded.json["question"]["id"] == second_id
    assert client.post(answer_path, json=first_answer).json == graded.json
    assert client.post(answer_path, json={"question_id": first_id, "answer": "Kyoto"}).status_code == 409

    second_answer = {"question_id": second_id, "answer": "8"}
    finished = client.post(answer_path, json=second_answer)
    assert finished.status_code == 200, finished.json
    assert finished.json["status"] == "completed"
    assert finished.json["score"] == 50
    assert finished.json["question"] is None
    assert client.post(answer_path, json=second_answer).json == finished.json

    with app.app_context():
        attempt = db.session.get(QuizAttempt, attempt_id)
        assert (attempt.user_id, attempt.quiz_id, attempt.score) == (student_id, quiz_id, 50)
        assert QuizQuestionAttempt.query.filter_by(quiz_attempt_id=attempt_id).count() == 2

    second_attempt = client.post(start_path)
    assert second_attempt.status_code == 201
    second_path = f"/api/quiz-attempts/{second_attempt.json['quiz_attempt_id']}/answers"
    assert client.post(second_path, json=first_answer).status_code == 200
    assert client.post(second_path, json={"question_id": second_id, "answer": "6"}).json["status"] == "completed"
    assert client.post(start_path).status_code == 409
    stats = client.get("/api/quizzes").json["quizzes"][0]
    assert (stats["last_score"], stats["average_score"]) == (100, 75)
    assert (stats["attempt_count"], stats["attempt_limit"], stats["can_resume"]) == (2, 2, False)
    other_stats = other_client.get("/api/quizzes").json["quizzes"][0]
    assert other_stats["attempt_count"] == 0
    assert other_stats["last_score"] is None
    assert other_client.post(start_path).status_code == 201
