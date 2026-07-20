from app import db
from app.models.models import StudyPlan, StudyPlanDay, StudyPlanProgress, User
from app.services import study_plan_service

# test were created with the help of AI
def _seed_user(test_app, username="planner", email="planner@example.com"):
    """Create a user row so study plan records have a valid owner FK."""
    with test_app.app_context():
        user = User(username=username, email=email, password_hash="hashed")
        db.session.add(user)
        db.session.commit()
        return user.id


def _fake_ai_plan(user_id, learning_context, days_until_exam=7):
    """Deterministic AI output used to keep tests fast and stable."""
    return {
        "title": "Test Plan",
        "days": [
            {
                "day_number": i + 1,
                "focus": f"Focus {i + 1}",
                "estimated_time_minutes": 45,
                "tasks": [
                    {"type": "note_review", "description": "Read notes"},
                    {"type": "quiz", "description": "Practice quiz"},
                ],
            }
            for i in range(days_until_exam)
        ],
    }


def test_generate_and_save_study_plan_persists_rows(test_app, monkeypatch):
    """Service test: plan generation should create plan, day rows, and progress in one flow."""
    user_id = _seed_user(test_app, username="serviceuser", email="service@example.com")
    monkeypatch.setattr(study_plan_service, "generate_study_plan_with_AI", _fake_ai_plan)

    with test_app.app_context():
        plan = study_plan_service.generate_and_save_study_plan(user_id=user_id, days_until_exam=7)

        # The parent StudyPlan row must be created.
        assert plan.id is not None
        assert plan.title == "Test Plan"
        assert plan.status == "active"

        # Exactly 7 day rows should exist, each with structured JSON tasks.
        days = StudyPlanDay.query.filter_by(study_plan_id=plan.id).order_by(StudyPlanDay.day_number.asc()).all()
        assert len(days) == 7
        assert days[0].task_json["focus"] == "Focus 1"
        assert len(days[0].task_json["tasks"]) >= 2

        # Progress should be initialized even before any completion actions.
        progress = StudyPlanProgress.query.filter_by(study_plan_id=plan.id, user_id=user_id).first()
        assert progress is not None
        assert progress.completed_days == 0
        assert progress.total_days == 7


def test_generate_and_save_study_plan_rejects_invalid_day_count(test_app, monkeypatch):
    """Service test: protects DB from malformed AI output with wrong day count."""
    user_id = _seed_user(test_app, username="badcount", email="badcount@example.com")

    def _bad_day_count(*args, **kwargs):
        return {
            "title": "Broken Plan",
            "days": [
                {
                    "day_number": 1,
                    "focus": "Only one day",
                    "estimated_time_minutes": 30,
                    "tasks": [
                        {"type": "note_review", "description": "Read"},
                        {"type": "quiz", "description": "Quiz"},
                    ],
                }
            ],
        }

    monkeypatch.setattr(study_plan_service, "generate_study_plan_with_AI", _bad_day_count)

    with test_app.app_context():
        try:
            study_plan_service.generate_and_save_study_plan(user_id=user_id, days_until_exam=7)
            assert False, "Expected ValueError for mismatched day count"
        except ValueError as exc:
            assert "expected 7 days" in str(exc)


def test_generate_study_plan_route_success(client, test_app, monkeypatch):
    """Route test: POST /study_plan/generate should return 200 and write records."""
    user_id = _seed_user(test_app, username="routegen", email="routegen@example.com")
    monkeypatch.setattr(study_plan_service, "generate_study_plan_with_AI", _fake_ai_plan)

    with client.session_transaction() as sess:
        sess["user_id"] = user_id
        sess["username"] = "routegen"

    response = client.post("/study_plan/generate", json={"days_until_exam": 7})
    data = response.get_json()

    assert response.status_code == 200
    assert data["message"] == "Study plan generated successfully."

    with test_app.app_context():
        assert StudyPlan.query.filter_by(user_id=user_id).count() == 1


def test_get_current_study_plan_route_returns_serialized_plan(client, test_app, monkeypatch):
    """Route test: GET /study_plan/current returns JSON-safe payload with day details."""
    user_id = _seed_user(test_app, username="routecurrent", email="routecurrent@example.com")
    monkeypatch.setattr(study_plan_service, "generate_study_plan_with_AI", _fake_ai_plan)

    with test_app.app_context():
        study_plan_service.generate_and_save_study_plan(user_id=user_id, days_until_exam=7)

    with client.session_transaction() as sess:
        sess["user_id"] = user_id
        sess["username"] = "routecurrent"

    response = client.get("/study_plan/current")
    data = response.get_json()

    assert response.status_code == 200
    assert data["title"] == "Test Plan"
    assert len(data["days"]) == 7
    assert data["days"][0]["day_number"] == 1


def test_complete_study_plan_day_route_updates_progress(client, test_app, monkeypatch):
    """Route test: completing a day should flip day completion and increment progress."""
    user_id = _seed_user(test_app, username="routecomplete", email="routecomplete@example.com")
    monkeypatch.setattr(study_plan_service, "generate_study_plan_with_AI", _fake_ai_plan)

    with test_app.app_context():
        plan = study_plan_service.generate_and_save_study_plan(user_id=user_id, days_until_exam=7)
        day_one = StudyPlanDay.query.filter_by(study_plan_id=plan.id, day_number=1).first()
        assert day_one.completed is False

    with client.session_transaction() as sess:
        sess["user_id"] = user_id
        sess["username"] = "routecomplete"

    response = client.post("/study_plan/day/complete", json={"day_number": 1})
    data = response.get_json()

    assert response.status_code == 200
    assert data["completed_days"] == 1
    assert data["total_days"] == 7
    assert data["plan_status"] == "active"

    with test_app.app_context():
        plan = StudyPlan.query.filter_by(user_id=user_id, status="active").first()
        day_one = StudyPlanDay.query.filter_by(study_plan_id=plan.id, day_number=1).first()
        assert day_one.completed is True


def test_complete_study_plan_day_rejects_duplicate_completion(client, test_app, monkeypatch):
    """Route test: same day cannot be completed twice; second call should return 400."""
    user_id = _seed_user(test_app, username="routedupe", email="routedupe@example.com")
    monkeypatch.setattr(study_plan_service, "generate_study_plan_with_AI", _fake_ai_plan)

    with test_app.app_context():
        study_plan_service.generate_and_save_study_plan(user_id=user_id, days_until_exam=7)

    with client.session_transaction() as sess:
        sess["user_id"] = user_id
        sess["username"] = "routedupe"

    first = client.post("/study_plan/day/complete", json={"day_number": 1})
    second = client.post("/study_plan/day/complete", json={"day_number": 1})

    assert first.status_code == 200
    assert second.status_code == 400
    assert "already marked as completed" in second.get_json()["error"]


def test_get_current_study_plan_returns_404_when_none(client):
    """Route test: if user has no plan, endpoint should return clear 404 response."""
    with client.session_transaction() as sess:
        sess["user_id"] = 999
        sess["username"] = "no-plan-user"

    response = client.get("/study_plan/current")
    assert response.status_code == 404
    assert "No active study plan found." in response.get_json()["error"]