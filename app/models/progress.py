"""Per-topic study progress tracked for each user."""

from datetime import datetime

from .. import db


class Progress(db.Model):
    """Record note-count progress for a user's topic."""

    __tablename__ = 'progress'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    topic_id = db.Column(db.Integer, db.ForeignKey('topic.id'), nullable=False)
    notes_count = db.Column(db.Integer, default=0)
    last_updated = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        """Summarize the tracked note count and topic for debugging."""
        return f'<Progress {self.notes_count} notes for Topic {self.topic_id}>'