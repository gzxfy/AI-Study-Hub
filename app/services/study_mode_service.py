import random
from app.models import FlashcardProgress, Flashcard
from app import db
from datetime import datetime

from app.utils.validation_helpers import validate_difficulty

def load_flashcards_for_study(user_id, note_id, difficulty=None, card_count=None):
    validate_difficulty(difficulty, card_count)
    
    query = Flashcard.query.filter_by(user_id=user_id, note_id=note_id)
    if difficulty:
        query = query.filter_by(difficulty=difficulty)

    cards = query.all()
    random.shuffle(cards)

    if card_count:
        cards = cards[:card_count]
    return cards

def start_study_mode(user_id, note_id, difficulty=None, card_count=None, priority=None):
    cards = load_flashcards_for_study(user_id=user_id, 
                                      note_id=note_id, 
                                      difficulty=difficulty,
                                      card_count=None)
    if priority and cards:
        cards_id = [card.id for card in cards]
        progress_rows = FlashcardProgress.query.filter(FlashcardProgress.user_id==user_id, FlashcardProgress.flashcard_id.in_(cards_id)).all()
        progress_by_card = {p.flashcard_id: p for p in progress_rows}

        def weakness_key(card):
            p = progress_by_card.get(card.id)
            if not p or p.times_seen == 0:
                return (0.0, 0)
            accuracy = p.times_correct / p.times_seen
            return (accuracy, p.times_seen)
        
        cards.sort(key=weakness_key)

        if card_count:
            cards = cards[:card_count]
    return cards


def review_flashcard(user_id, flashcard, marked_correctly):
    flashcard = Flashcard.query.filter_by(id=flashcard.id, user_id=user_id).first()
    if not flashcard:
        raise ValueError("Flashcard not found.")
    
    progress = FlashcardProgress.query.filter_by(user_id=user_id, flashcard_id=flashcard.id).first()
    if not progress:
        progress = FlashcardProgress(user_id=user_id, flashcard_id=flashcard.id, times_seen=0, times_correct=0, streak=0, progress=0)
        db.session.add(progress)  # Add the new progress record to the session
    
    progress.times_seen += 1
    if marked_correctly:
        progress.times_correct += 1
        progress.streak += 1
    else:
        progress.streak = 0  # Reset the streak if answered incorrectly

    progress.progress = progress.times_correct / progress.times_seen if progress.times_seen > 0 else 0  # Update the progress as a fraction of correct answers
    progress.last_seen = datetime.utcnow()  # Update the last seen timestamp
    db.session.commit()
    return progress

def end_study_mode(user_id, reviewed_results):
    reviewed_count = len(reviewed_results)
    correct_count = sum(1 for result in reviewed_results if result.get("correct"))
    accuracy = round((correct_count / reviewed_count) * 100, 2) if reviewed_count > 0 else 0

    return {
        "user_id": user_id,
        "reviewed_count": reviewed_count,
        "correct_count": correct_count,
        "accuracy": accuracy
    }
