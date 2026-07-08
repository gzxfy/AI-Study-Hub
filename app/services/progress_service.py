import app.utils.validation_helpers as validation_helpers
from app.models.models import FlashcardProgress

def get_flashcard_progress(user_id, flashcard_id):
    return FlashcardProgress.query.filter_by(user_id=user_id, flashcard_id=flashcard_id).first()

def get_user_progress(user_id):
    records = FlashcardProgress.query.filter_by(user_id=user_id).all()
    
    total_reviewed = sum(p.times_seen for p in records) 
    total_correct = sum(p.times_correct for p in records)
    average_accuracy = round((total_correct / total_reviewed) * 100, 2) if total_reviewed > 0 else 0
    cards_mastered = sum(1 for p in records if p.times_seen > 5 and (p.times_correct / p.times_seen) >= 0.8)
    cards_needing_reviewing = sum(1 for p in records if p.times_seen > 0 and (p.times_correct / p.times_seen) < 0.6)
    
    return {
        "total_cards": len(records),
        "total_reviewed": total_reviewed,
        "average_accuracy": average_accuracy,
        "cards_mastered": cards_mastered,
        "cards_needing_reviewing": cards_needing_reviewing
        # "current_streak": max(p.current_streak for p in records) if records else 0
    }

# Function to get the current streak for a user will be implemented during the study session feature development.