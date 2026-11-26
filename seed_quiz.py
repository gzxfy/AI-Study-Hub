import os

from sqlalchemy import text

from backend import create_app, db
from backend.models import Quiz, QuizQuestion

# Seed function for the General Knowledge quiz
def seed_general_knowledge():
    existing_quiz = Quiz.query.filter_by(
        title="General Knowledge",
        user_id=None,
    ).first()

    if existing_quiz is not None:
        print(f"General Knowledge already exists (id={existing_quiz.id}).")
        return

    quiz = Quiz(
        title="General Knowledge",
        description="A short quiz covering a mix of topics.",
        user_id=None,
        is_active=True,
    )
    db.session.add(quiz)
    db.session.flush()

    db.session.add_all([
        QuizQuestion(
            quiz_id=quiz.id,
            question_text="What is the capital of Japan?",
            correct_answer="Tokyo",
        ),
        QuizQuestion(
            quiz_id=quiz.id,
            question_text="How many sides does a hexagon have?",
            correct_answer="6",
        ),
    ])

    db.session.commit()
    print(f"Created General Knowledge (id={quiz.id}) with 2 questions.")

# Main execution block for seeding the General Knowledge quiz
if __name__ == "__main__":
    database_url = os.getenv("SEED_DATABASE_URL")
    if not database_url:
        raise SystemExit("Set SEED_DATABASE_URL to your scratch database URL.")

    app = create_app({"SQLALCHEMY_DATABASE_URI": database_url})

    with app.app_context():
        database_name = db.session.execute(
            text("SELECT current_database()")
        ).scalar_one()

        if database_name != "studyhub_migration_scratch":
            raise SystemExit("This seed script only runs on studyhub_migration_scratch.")

        seed_general_knowledge()