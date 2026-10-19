"""Flashcard prompts and answers created from a user's study notes."""

from datetime import datetime

from .. import db


class Flashcard(db.Model):
    """Store a review question, answer, and optional topic and difficulty."""

    __tablename__ = 'flashcards'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    topic_id = db.Column(db.Integer, db.ForeignKey('topic.id'), nullable=True)
    note_id = db.Column(db.Integer, db.ForeignKey('notes.id'), nullable=False)
    question = db.Column(db.Text, nullable=False)
    answer = db.Column(db.Text, nullable=False)
    difficulty = db.Column(db.String(50), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        """Show a short prompt preview and difficulty in debugging output."""
        return f'<Flashcard {self.question[:20]}... Difficulty: {self.difficulty}>'