"""A learner's response to one flashcard question in a quiz."""

from datetime import datetime

from .. import db


class QuizQuestionAttempt(db.Model):
    """Store the submitted answer, correctness, and response time."""

    __tablename__ = 'quiz_question_attempts'

    id = db.Column(db.Integer, primary_key=True)
    quiz_attempt_id = db.Column(db.Integer, db.ForeignKey('quiz_attempts.id'), nullable=False)
    flashcard_id = db.Column(db.Integer, db.ForeignKey('flashcards.id'), nullable=True)
    quiz_question_id = db.Column(db.Integer, db.ForeignKey('quiz_questions.id'), nullable=True)

    user_answer = db.Column(db.Text, nullable=False)
    correct_answer = db.Column(db.Text, nullable=False)
    is_correct = db.Column(db.Boolean, default=False)
    time_taken = db.Column(db.Float, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (
            db.CheckConstraint(
            "(flashcard_id IS NOT NULL AND quiz_question_id IS NULL) OR "
            "(flashcard_id IS NULL AND quiz_question_id IS NOT NULL)",
            name="ck_quiz_question_attempt_exactly_one_source",
            ),
        )

    def __repr__(self):
        """Identify the quiz and flashcard response in debugging output."""
        return f'<QuizQuestionAttempt {self.id} for QuizAttempt {self.quiz_attempt_id} Flashcard {self.flashcard_id}>'
