from datetime import datetime, timedelta
from app.models.models import (
    Note, Flashcard, QuizAttempt,
    StudyPlan, StudyPlanDay, StudyPlanProgress, db
)
from app.services.ai_service import generate_study_plan_with_AI



def collect_user_learning_context(user_id):
    """
    Collects the learning context for a given user.

    Args:
        user_id (int): The ID of the user.
    """

    # Fetch all notes for the user
    notes = Note.query.filter_by(user_id=user_id).all()

    # Fetch all flashcards for the user
    flashcards = Flashcard.query.filter_by(user_id=user_id).all()

    # Fetch all quizzes for the user
    quizzes = QuizAttempt.query.filter_by(user_id=user_id).all()

    # fetch topic that the user is studying
    topics = sorted({n.topic.title for n in notes if n.topic and n.topic.title})

    # Combine all learning context data into a dictionary
    learning_context = {
        "notes": notes,
        "flashcards": flashcards,
        "quizzes": quizzes,
        "topics": topics
    }

    return learning_context

def generate_and_save_study_plan(user_id, days_until_exam=7, start_date=None):
    """
    Generates a study plan for the user and saves it to the database.

    Args:
        user_id (int): The ID of the user.
        days_until_exam (int): Number of days until the exam.
        start_date (datetime, optional): The start date for the study plan. Defaults to today.
    """

    learning_context = collect_user_learning_context(user_id)
    plan_data = generate_study_plan_with_AI(user_id, learning_context, days_until_exam=days_until_exam)

    start = start_date or datetime.utcnow()
    end = start + timedelta(days=days_until_exam - 1)

    plan = StudyPlan(
        user_id=user_id,
        title=plan_data.get("title", "Personalized Study Plan"),
        start_date=start,
        end_date=end,
        status="active",
    )
    db.session.add(plan)
    db.session.flush()

    for day in plan_data["days"]:
        day_number = int(day["day_number"])
        date_for_day = start + timedelta(days=day_number - 1)

        row = StudyPlanDay(
            study_plan_id=plan.id,
            day_number=day_number,
            date=date_for_day,
            task_json={
                "focus": day.get("focus", ""),
                "tasks": day.get("tasks", []),
            },
            estimated_time_minutes=int(day.get("estimated_time_minutes", 60)),
        )
        tasks = day.get("tasks", [])
        if not isinstance(tasks, list) or len(tasks) < 2:
            raise ValueError(f"invalid tasks for day {day_number}")
        db.session.add(row)

    progress = StudyPlanProgress(
        study_plan_id=plan.id,
        user_id=user_id,
        completed_days=0,
        total_days=days_until_exam,
    )
    db.session.add(progress)

    db.session.commit()
    return plan