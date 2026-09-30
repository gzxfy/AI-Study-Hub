"""Individual user or assistant messages in a conversation."""

from datetime import datetime

from .. import db


class Message(db.Model):
    """Store one role-tagged message belonging to an AI conversation."""

    __tablename__ = 'messages'

    id = db.Column(db.Integer, primary_key=True)
    conversation_id = db.Column(db.Integer, db.ForeignKey('conversations.id'), nullable=False)
    role = db.Column(db.String(20), nullable=False)
    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        """Identify the message role and conversation in debugging output."""
        return f'<Message {self.role} in Conversation {self.conversation_id}>'