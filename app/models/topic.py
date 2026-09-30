"""Study topics used to organize notes, flashcards, and progress."""

from datetime import datetime

from .. import db


class Topic(db.Model):
    """Represent a subject area owned by a user."""

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    color = db.Column(db.String(7), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    notes = db.relationship('Note', backref='topic', cascade="all, delete-orphan")
    progress = db.relationship('Progress', backref='topic', cascade="all, delete-orphan")
    flashcards = db.relationship('Flashcard', backref='topic', cascade="all, delete-orphan")

    def __repr__(self):
        """Identify the topic in ORM and debugging output."""
        return f'<Topic {self.title}>'