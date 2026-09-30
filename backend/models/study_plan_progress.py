"""Aggregate day-completion progress for a user's study plan."""

from datetime import datetime

from .. import db


class StudyPlanProgress(db.Model):
    """Track completed and total days for an individual study plan."""

    __tablename__ = 'study_plan_progress'

    id = db.Column(db.Integer, primary_key=True)
    study_plan_id = db.Column(db.Integer, db.ForeignKey('study_plans.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    completed_days = db.Column(db.Integer, default=0)
    total_days = db.Column(db.Integer, default=0)
    last_updated = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        """Identify the study plan and user in debugging output."""
        return f'<StudyPlanProgress for StudyPlan {self.study_plan_id} User {self.user_id}>'