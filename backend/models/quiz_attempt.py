"""A user's quiz session and its ordered questions and score."""

from datetime import datetime

from .. import db


class QuizAttempt(db.Model):
    """Track quiz state, selected questions, score, and completion times."""

    __tablename__ = 'quiz_attempts'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    topic_id = db.Column(db.Integer, db.ForeignKey('topic.id'), nullable=True)
    note_id = db.Column(db.Integer, db.ForeignKey('notes.id'), nullable=False)
    score = db.Column(db.Float, default=0)
    status = db.Column(db.String(20), default='in_progress')
    question_index = db.Column(db.Integer, default=0)
    question_order = db.Column(db.JSON, nullable=True)
    started_at = db.Column(db.DateTime, default=datetime.utcnow)
    finished_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    question_attempts = db.relationship('QuizQuestionAttempt', backref='quiz_attempt', cascade='all, delete-orphan')

    def __repr__(self):
        """Summarize the quiz note, topic, and score in debugging output."""
        return f'<QuizAttempt {self.id} for Note {self.note_id} Topic {self.topic_id} Score: {self.score}>'