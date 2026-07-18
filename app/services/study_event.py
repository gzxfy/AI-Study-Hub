import app.utils.validation_helpers as validation_helpers
from app.models.models import StudyEvent, db
from datetime import datetime

def log_study_event(user_id, flashcard_id, is_correct, source=None):
    # Validate inputs
    validation_helpers.validate_study_event_data(user_id, flashcard_id, is_correct, source)

    # Create a new StudyEvent instance
    study_event = StudyEvent(
        user_id=user_id,
        flashcard_id=flashcard_id,
        is_correct=is_correct,
        source=source
    )

    # Add the study event to the session and commit
    db.session.add(study_event)
    db.session.commit()

    return study_event

def get_study_events(user_id, flashcard_id=None):
    query = StudyEvent.query.filter_by(user_id=user_id)
    if flashcard_id:
        query = query.filter_by(flashcard_id=flashcard_id)
    return query.all()

def cards_studied_today(user_id):
    today = datetime.utcnow().date()
    return StudyEvent.query.filter(
        StudyEvent.user_id == user_id,
        db.func.date(StudyEvent.studied_at) == today
    ).count()

def current_streak(user_id):
    # Get all study events for the user, ordered by date
    events = StudyEvent.query.filter_by(user_id=user_id).order_by(StudyEvent.studied_at.desc()).all()
    
    streak = 0
    last_date = None
    
    for event in events:
        event_date = event.studied_at.date()
        if last_date is None:
            last_date = event_date
            streak += 1
        else:
            # Check if the event date is the day before the last date
            if (last_date - event_date).days == 1:
                streak += 1
                last_date = event_date
            elif (last_date - event_date).days > 1:
                break  # Streak is broken
    
    return streak


def average_accuracy(user_id):
    events = StudyEvent.query.filter_by(user_id=user_id).all()
    if not events:
        return 0.0
    correct_count = sum(1 for event in events if event.is_correct)
    return (correct_count / len(events)) * 100

def cards_mastered(user_id):
    # A card is considered mastered if it has been answered correctly at least 5 times
    mastered_flashcards = db.session.query(StudyEvent.flashcard_id).filter_by(user_id=user_id, is_correct=True).group_by(StudyEvent.flashcard_id).having(db.func.count(StudyEvent.id) >= 5).all()
    return len(mastered_flashcards)

def cards_needing_review(user_id):
    # A card needs review if it has a low accuracy rate 
    needing_review_flashcards = db.session.query(StudyEvent.flashcard_id).filter_by(user_id=user_id, is_correct=False).group_by(StudyEvent.flashcard_id).having(db.func.count(StudyEvent.id) > 4).all()
    return len(needing_review_flashcards)