import app.utils.validation_helpers as validation_helpers
from app.models.models import StudyEvent, db
from datetime import date, datetime, timedelta

def log_study_event(user_id, flashcard_id, is_correct, source=None, studied_at=None):
    # Validate inputs
    validation_helpers.validate_study_event_data(user_id, flashcard_id, is_correct, source)

    # Create a new StudyEvent instance
    study_event = StudyEvent(
        user_id=user_id,
        flashcard_id=flashcard_id,
        is_correct=is_correct,
        source=source,
        studied_at=studied_at or datetime.utcnow()  # Use UTC time for consistency
    )

    # Add the study event to the session and commit
    db.session.add(study_event)
    return study_event

def get_study_events(user_id, flashcard_id=None):
    query = StudyEvent.query.filter_by(user_id=user_id)
    if flashcard_id:
        query = query.filter_by(flashcard_id=flashcard_id)
    return query.all()

def cards_studied_today(user_id):
    today = datetime.utcnow().date()
    return (
        db.session.query(db.func.count(db.distinct(StudyEvent.flashcard_id)))
        .filter(
            StudyEvent.user_id == user_id,
            db.func.date(StudyEvent.studied_at) == today
        )
        .scalar()
    )

# this was made with the help of chatgpt, it is not tested yet
def current_streak(user_id):
    # Get all distinct study event dates for the user, ordered from most recent to oldest
    raw_dates = (
        db.session.query(db.func.date(StudyEvent.studied_at))
        .filter(StudyEvent.user_id == user_id)
        .distinct()
        .order_by(db.func.date(StudyEvent.studied_at).desc())
        .all()
    )

    if not raw_dates:
        return 0

    # Normalize DB output to Python date objects
    dates = []
    for row in raw_dates:
        value = row[0]
        if isinstance(value, str):
            dates.append(datetime.strptime(value, "%Y-%m-%d").date())
        elif isinstance(value, datetime):
            dates.append(value.date())
        elif isinstance(value, date):
            dates.append(value)

    if not dates:
        return 0

    # Check if the most recent date is today or yesterday; if not, streak is 0
    today = datetime.utcnow().date()
    if dates[0] not in (today, today - timedelta(days=1)):
        return 0

    # Calculate the streak by iterating through the dates
    streak = 1
    for i in range(1, len(dates)):
        if (dates[i - 1] - dates[i]).days == 1:
            streak += 1
        else:
            break

    return streak