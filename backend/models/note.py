"""Study notes and their related conversations and flashcards."""

from datetime import datetime

from .. import db


class Note(db.Model):
    """Store a user's study material and optional uploaded PDF path."""

    __tablename__ = 'notes'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    topic_id = db.Column(db.Integer, db.ForeignKey('topic.id'), nullable=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    uploaded_pdf_path = db.Column(db.String(500), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    conversation = db.relationship('Conversation', backref='note', cascade='all, delete-orphan', uselist=False)
    flashcards = db.relationship('Flashcard', backref='note', cascade="all, delete-orphan")

    def __repr__(self):
        """Identify the note in ORM and debugging output."""
        return f'<Note {self.title}>'