"""User identity and ownership relationships for study data."""

from datetime import datetime

from flask_login import UserMixin

from .. import db


class User(UserMixin, db.Model):
    """Store login identity and own the user's study resources."""

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    topics = db.relationship('Topic', backref='user', cascade="all, delete-orphan")
    notes = db.relationship('Note', backref='user', cascade="all, delete-orphan")
    conversations = db.relationship('Conversation', backref='user', cascade="all, delete-orphan")
    progress = db.relationship('Progress', backref='user', cascade="all, delete-orphan")
    flashcards = db.relationship('Flashcard', backref='user', cascade="all, delete-orphan")

    def __repr__(self):
        """Identify the user in ORM and debugging output."""
        return f'<User {self.username}>'