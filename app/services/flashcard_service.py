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

def edit_flashcard(flashcard_id, user_id, question=None, answer=None, difficulty=None):
    flashcard = get_flashcard_by_id(flashcard_id, user_id)
    if not flashcard:
        raise ValueError("Flashcard not found.")
    if flashcard.user_id != user_id:
        raise ValueError("You do not have permission to edit this flashcard.")
    if question is not None and answer is not None and difficulty is not None:
        flashcard.question = question
        flashcard.answer = answer
        flashcard.difficulty = difficulty
    validation_helpers.validate_flashcard_data(flashcard.question, flashcard.answer, flashcard.difficulty)
    db.session.commit()
    return flashcard

def delete_flashcard(flashcard_id, user_id):
    flashcard = get_flashcard_by_id(flashcard_id, user_id)
    if not flashcard:
        raise ValueError("Flashcard not found.")
    if flashcard.user_id != user_id:
        raise ValueError("You do not have permission to delete this flashcard.")
    db.session.delete(flashcard)
    db.session.commit()
    return flashcard