from backend.models.models import Flashcard, db
import backend.utils.validation_helpers as validation_helpers

def create_flashcard(user_id, topic_id, note_id, question, answer, difficulty=None):
    """Validate and persist a flashcard associated with a user's note."""
    validation_helpers.validate_flashcard_data(question, answer, difficulty)
    flashcard = Flashcard(user_id=user_id, topic_id=topic_id, note_id=note_id, question=question, answer=answer, difficulty=difficulty)
    db.session.add(flashcard)
    db.session.commit()
    return flashcard

def get_flashcard_by_id(flashcard_id, user_id=None):
    """Fetch a flashcard, optionally restricting the result to its owner."""
    flashcard = Flashcard.query.get(flashcard_id)
    if user_id and flashcard and flashcard.user_id != user_id:
        return None
    return flashcard

def get_all_flashcards(user_id):
    """Return all flashcards owned by the requested user."""
    return Flashcard.query.filter_by(user_id=user_id).all()

def edit_flashcard(flashcard_id, user_id, question=None, answer=None, difficulty=None):
    """Validate and save updates to a flashcard owned by the user."""
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
    """Remove a flashcard after confirming that it belongs to the user."""
    flashcard = get_flashcard_by_id(flashcard_id, user_id)
    if not flashcard:
        raise ValueError("Flashcard not found.")
    if flashcard.user_id != user_id:
        raise ValueError("You do not have permission to delete this flashcard.")
    db.session.delete(flashcard)
    db.session.commit()
    return flashcard


