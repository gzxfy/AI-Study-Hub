from app.models.models import Flashcard, db
import app.utils.validation_helpers as validation_helpers

def create_flashcard(user_id, topic_id, note_id, question, answer, difficulty=None):
    validation_helpers.validate_flashcard_data(question, answer, difficulty)
    flashcard = Flashcard(user_id=user_id, topic_id=topic_id, note_id=note_id, question=question, answer=answer, difficulty=difficulty)
    db.session.add(flashcard)
    db.session.commit()
    return flashcard

def get_flashcard_by_id(flashcard_id, user_id=None):
    flashcard = Flashcard.query.get(flashcard_id)
    if user_id and flashcard and flashcard.user_id != user_id:
        return None
    return flashcard

def get_all_flashcards(user_id):
    return Flashcard.query.filter_by(user_id=user_id).all()