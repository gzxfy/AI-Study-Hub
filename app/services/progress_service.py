from app.models.models import FlashcardProgress
import app.services.study_event as study_event_service

def get_flashcard_progress(user_id, flashcard_id):
    return FlashcardProgress.query.filter_by(user_id=user_id, flashcard_id=flashcard_id).first()

def get_user_progress(user_id):
    records = FlashcardProgress.query.filter_by(user_id=user_id).all()
    
    total_reviewed = sum(p.times_seen for p in records) 
    total_correct = sum(p.times_correct for p in records)
    average_accuracy = round((total_correct / total_reviewed) * 100, 2) if total_reviewed > 0 else 0
    cards_mastered = sum(1 for p in records if p.times_seen > 5 and (p.times_correct / p.times_seen) >= 0.8)
    cards_needing_reviewing = sum(1 for p in records if p.times_seen > 0 and (p.times_correct / p.times_seen) < 0.6)
    
    cards_studied_today = study_event_service.cards_studied_today(user_id)
    streak = study_event_service.current_streak(user_id)
    
    return {
        "total_cards": len(records),
        "total_reviewed": total_reviewed,
        "average_accuracy": average_accuracy,
        "cards_mastered": cards_mastered,
        "cards_needing_reviewing": cards_needing_reviewing,
        "cards_studied_today": cards_studied_today,
        "current_streak": streak
    }

