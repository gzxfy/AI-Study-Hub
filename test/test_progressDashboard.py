from datetime import datetime, date, timedelta

from app import db
from app.models.models import Flashcard, FlashcardProgress, Note, StudyEvent, User
from app.services import progress_service, study_event

def _seed_user_note_flashcard(username, email):
    user = User(
        username=username,
        email=email,
        password_hash="hashed-password",
    )
    db.session.add(user)
    db.session.flush()

    note = Note(user_id=user.id, title="Seed Note", content="Seed note content")
    db.session.add(note)
    db.session.flush()

    flashcard = Flashcard(
        user_id=user.id,
        note_id=note.id,
        question="Question 1",
        answer="Answer 1",
        difficulty="easy",
    )
    db.session.add(flashcard)
    db.session.flush()

    return user, note, flashcard
 
def test_user_progress(test_app):
    # made with the help of the AI
    with test_app.app_context():
        user = User(
            username='testuser',
            email='testuser@example.com',
            password_hash='hashed-password'
        )
        db.session.add(user)
        db.session.flush()

        note = Note(user_id=user.id, title='Progress Note', content='Seed note content')
        db.session.add(note)
        db.session.flush()

        flashcard1 = Flashcard(
            user_id=user.id,
            note_id=note.id,
            question='Question 1',
            answer='Answer 1',
            difficulty='easy'
        )
        flashcard2 = Flashcard(
            user_id=user.id,
            note_id=note.id,
            question='Question 2',
            answer='Answer 2',
            difficulty='medium'
        )
        db.session.add(flashcard1)
        db.session.add(flashcard2)
        db.session.flush()

        progress1 = FlashcardProgress(user_id=user.id, flashcard_id=flashcard1.id, times_seen=5, times_correct=2)
        progress2 = FlashcardProgress(user_id=user.id, flashcard_id=flashcard2.id, times_seen=3, times_correct=3)

        db.session.add(progress1)
        db.session.add(progress2)
        db.session.commit()

        stats = progress_service.get_user_progress(user_id=user.id)
        assert stats['total_cards'] == 2
        assert stats['total_reviewed'] == 8
        assert stats['average_accuracy'] == 62.5
        assert stats['cards_mastered'] == 0
        assert stats['cards_needing_reviewing'] == 1
        assert stats['cards_studied_today'] == 0
        assert stats['current_streak'] == 0

def test_current_streak_today_and_yesterday(test_app):
    with test_app.app_context():
        user, _note, flashcard = _seed_user_note_flashcard(
            username="streakuser",
            email="streakuser@example.com",
        )

        now = datetime.utcnow().replace(microsecond=0)
        yesterday = now - timedelta(days=1)

        e1 = StudyEvent(
            user_id=user.id,
            flashcard_id=flashcard.id,
            is_correct=True,
            source="study_mode",
            studied_at=now,
        )
        e2 = StudyEvent(
            user_id=user.id,
            flashcard_id=flashcard.id,
            is_correct=False,
            source="quiz",
            studied_at=yesterday,
        )
        db.session.add_all([e1, e2])
        db.session.commit()

        stats = progress_service.get_user_progress(user_id=user.id)

        assert stats["cards_studied_today"] == 1
        assert stats["current_streak"] == 2

def test_studied_today(test_app):
    with test_app.app_context():
        user, _note, flashcard = _seed_user_note_flashcard(
            username="todayuser",
            email="todayuser@example.com",
        )

        now = datetime.utcnow().replace(microsecond=0)

        e1 = StudyEvent(
            user_id=user.id,
            flashcard_id=flashcard.id,
            is_correct=True,
            source="study_mode",
            studied_at=now,
        )
        db.session.add(e1)
        db.session.commit()

        stats = progress_service.get_user_progress(user_id=user.id)

        assert stats["cards_studied_today"] == 1