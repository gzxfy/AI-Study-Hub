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

    if not isinstance(plan_data, dict):
        raise ValueError("Study plan generation failed: invalid AI payload.")

    if "days" not in plan_data or not isinstance(plan_data["days"], list):
        raise ValueError("Study plan generation failed: missing days array.")
    if len(plan_data["days"]) != days_until_exam:
        raise ValueError(f"Study plan generation failed: expected {days_until_exam} days.")
    
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

def get_current_study_plan(user_id):
    """
    Retrieves the current active study plan for the user.

    Args:
        user_id (int): The ID of the user.
    """
    current_plan = StudyPlan.query.filter_by(user_id=user_id, status="active").first()
    if not current_plan:
        return None
    return current_plan
    
def complete_study_plan_day(user_id, day_number):
    """
    Marks a specific day in the user's study plan as completed.

    Args:
        user_id (int): The ID of the user.
        day_number (int): The day number to mark as completed.
    """
    current_plan = StudyPlan.query.filter_by(user_id=user_id, status="active").first()
    if not current_plan:
        raise ValueError("No active study plan found.")

    day = StudyPlanDay.query.filter_by(study_plan_id=current_plan.id, day_number=day_number).first()
    if not day:
        raise ValueError(f"Day {day_number} not found in the current study plan.")

    if day.completed:
        raise ValueError(f"Day {day_number} is already marked as completed.")

    day.completed = True
    progress = StudyPlanProgress.query.filter_by(study_plan_id=current_plan.id, user_id=user_id).first()
    progress.completed_days += 1

    if progress.completed_days >= progress.total_days:
        current_plan.status = "completed"

    db.session.commit()

    return {
        "completed_days": progress.completed_days,
        "total_days": progress.total_days,
        "plan_status": current_plan.status
    }
def delete_study_plan(user_id, study_plan_id=None):
    """
    Deletes the current active study plan for the user.

    Args:
        user_id (int): The ID of the user.
    """
    if study_plan_id:
        try:
            study_plan_id = int(study_plan_id)
        except (TypeError, ValueError):
            raise ValueError("study_plan_id must be a valid integer.")
        current_plan = StudyPlan.query.filter_by(user_id=user_id, id=study_plan_id).first()
    else:
        current_plan = StudyPlan.query.filter_by(user_id=user_id, status="active").first()
    if not current_plan:
        raise ValueError("No active study plan found.")

    # Delete associated days and progress
    StudyPlanDay.query.filter_by(study_plan_id=current_plan.id).delete()
    StudyPlanProgress.query.filter_by(study_plan_id=current_plan.id).delete()

    # Delete the study plan itself
    db.session.delete(current_plan)
    db.session.commit()

def get_study_plan_progress(user_id, study_plan_id=None):
    """
    Retrieves the progress of the current active study plan for the user.

    Args:
        user_id (int): The ID of the user.
    """
    if study_plan_id:
        try:
            study_plan_id = int(study_plan_id)
        except (TypeError, ValueError):
            raise ValueError("study_plan_id must be a valid integer.")
        current_plan = StudyPlan.query.filter_by(user_id=user_id, id=study_plan_id).first()
    else:
        current_plan = StudyPlan.query.filter_by(user_id=user_id, status="active").first()
    if not current_plan:
        raise ValueError("No active study plan found.")

    progress = StudyPlanProgress.query.filter_by(study_plan_id=current_plan.id, user_id=user_id).first()
    if not progress:
        raise ValueError("Progress record not found for the current study plan.")

    return {
        "completed_days": progress.completed_days,
        "total_days": progress.total_days,
        "plan_status": current_plan.status
    }