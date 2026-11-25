"""
Quiz model for the AI Study Hub application.
"""

from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, Float
from datetime import datetime
from .. import db

class Quiz(db.Model):
    __tablename__ = "quizzes"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, db.ForeignKey('user.id'), nullable=True)
    
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    attempt_count = Column(Integer, default=0)
    average_score = Column(Float, default=0)
    is_active = Column(Boolean, default=True)
    last_score = Column(Float, default=0)

    last_attempted_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        """Summarize the quiz title, note, and topic in debugging output."""
        return f'<Quiz {self.id} Title: {self.title}>'