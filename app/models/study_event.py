"""Timestamped records of flashcard study activity."""

from datetime import datetime

from .. import db


class StudyEvent(db.Model):
    """Record whether a user answered a flashcard correctly and its source."""

    __tablename__ = 'study_events'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    flashcard_id = db.Column(db.Integer, db.ForeignKey('flashcards.id'), nullable=False)
    studied_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_correct = db.Column(db.Boolean, nullable=False)
    source = db.Column(db.String(50), nullable=True)

    def __repr__(self):
        """Summarize the learner, flashcard, and result for debugging."""
        return f'<StudyEvent User {self.user_id} Flashcard {self.flashcard_id} Correct: {self.is_correct}>'