"""Per-user review statistics associated with individual flashcards."""

from datetime import datetime

from .. import db


class FlashcardProgress(db.Model):
    """Track review counts, correctness streak, and mastery for a flashcard."""

    __tablename__ = 'flashcard_progress'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    flashcard_id = db.Column(db.Integer, db.ForeignKey('flashcards.id'), nullable=False)
    times_seen = db.Column(db.Integer, default=0)
    times_correct = db.Column(db.Integer, default=0)
    streak = db.Column(db.Integer, default=0)
    progress = db.Column(db.Integer, default=0)
    last_seen = db.Column(db.DateTime, default=datetime.utcnow)
    last_updated = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)