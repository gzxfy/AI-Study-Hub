import app.utils.validation_helpers as validation_helpers
from app.models.models import FlashcardProgress

def get_total_cards_reviewed(user_id):
    return FlashcardProgress.query.filter_by(user_id=user_id).count()

def get_accuracy(user_id):
    pass