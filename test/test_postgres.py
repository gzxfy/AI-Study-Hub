from sqlalchemy import text
from backend import db

def test_postgres_connection(empty_postgres_app):
    with empty_postgres_app.app_context():
        database = db.session.execute(text("SELECT current_database()")).scalar_one()
        assert database.startswith("studyhub_test_")
        assert database == db.engine.url.database
