"""Daily schedule entries and tasks belonging to a study plan."""

from .. import db


class StudyPlanDay(db.Model):
    """Store one scheduled day's tasks, duration estimate, and completion."""

    __tablename__ = 'study_plan_days'

    study_plan_id = db.Column(db.Integer, db.ForeignKey('study_plans.id'), primary_key=True)
    day_number = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.DateTime, nullable=False)
    task_json = db.Column(db.JSON, nullable=True)
    estimated_time_minutes = db.Column(db.Integer, nullable=True)
    completed = db.Column(db.Boolean, default=False, nullable=False)

    def __repr__(self):
        """Identify the day within its plan in debugging output."""
        return f'<StudyPlanDay {self.day_number} for StudyPlan {self.study_plan_id}>'