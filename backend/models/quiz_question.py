"""Quiz question model for the AI Study Hub application."""

from datetime import datetime

from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, Float
from .. import db

class QuizQuestion(db.Model):
    __tablename__ = "quiz_questions"

    id = Column(Integer, primary_key=True, index=True)
    quiz_id = Column(Integer, db.ForeignKey('quizzes.id'), nullable=False)
    

    question_text = Column(Text, nullable=False)
    question_type = Column(String, nullable=True)
    correct_answer = Column(Text, nullable=False)
    difficulty = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        """Summarize the quiz question in debugging output."""
        return f'<QuizQuestion {self.id} for Quiz {self.quiz_id}>'