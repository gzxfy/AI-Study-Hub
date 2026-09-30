"""AI assistant conversation sessions attached to study notes."""

from datetime import datetime

from .. import db


class Conversation(db.Model):
    """Group messages exchanged while studying a note with the AI."""

    __tablename__ = 'conversations'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    note_id = db.Column(db.Integer, db.ForeignKey('notes.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    messages = db.relationship('Message', backref='conversation', lazy=True, cascade='all, delete-orphan')

    def __repr__(self):
        """Identify this session and its note in debugging output."""
        return f'<Conversation {self.id} for Note {self.note_id}>'