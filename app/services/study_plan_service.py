from app.models.models import Note, StudyEvent, QuizAttempt, db


def collect_user_learning_context(user_id):
    """
    Collects the learning context for a given user.

    Args:
        user_id (int): The ID of the user.
    """

    # Fetch all notes for the user
    notes = Note.query.filter_by(user_id=user_id).all()

    # Fetch all study events for the user
    study_events = StudyEvent.query.filter_by(user_id=user_id).all()

    # Fetch all quizzes for the user
    quizzes = QuizAttempt.query.filter_by(user_id=user_id).all()

    # Combine all learning context data into a dictionary
    learning_context = {
        "notes": notes,
        "study_events": study_events,
        "quizzes": quizzes
    }

    return learning_context