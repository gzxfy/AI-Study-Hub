import os
from uuid import uuid4

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url

from backend import create_app, db

@pytest.fixture
def empty_postgres_app():
    test_database_url = os.getenv('TEST_DATABASE_URL')
    if not test_database_url:
        pytest.skip("TEST_DATABASE_URL is not set")

    url = make_url(test_database_url)
    if url.get_backend_name() != "postgresql" or url.database != "studyhub_test":
        pytest.fail("TEST_DATABASE_URL must point to PostgreSQL database studyhub_test", pytrace=False)

    # Only the database generated for this test is ever dropped.
    database = f"studyhub_test_{uuid4().hex}"
    admin_engine = create_engine(url, isolation_level="AUTOCOMMIT")
    try:
        with admin_engine.connect() as connection:
            if connection.scalar(text("SELECT current_database()")) != "studyhub_test":
                pytest.fail("Connected to an unexpected PostgreSQL database", pytrace=False)
            connection.exec_driver_sql(f'CREATE DATABASE "{database}"')
            try:
                yield from _postgres_test_app(url.set(database=database))
            finally:
                connection.exec_driver_sql(f'DROP DATABASE "{database}"')
    finally:
        admin_engine.dispose()


def _postgres_test_app(url):
    app = create_app({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': url.render_as_string(hide_password=False),
        'WTF_CSRF_ENABLED': False
    })
    try:
        yield app
    finally:
        with app.app_context():
            db.session.remove()
            db.engine.dispose()


@pytest.fixture
def postgres_app(empty_postgres_app):
    with empty_postgres_app.app_context():
        db.create_all()
    return empty_postgres_app


@pytest.fixture
def test_app():
    app = create_app({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
        'WTF_CSRF_ENABLED': False
    })
    
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()

@pytest.fixture
def client(test_app):
    return test_app.test_client()   

@pytest.fixture
def runner(test_app):
    return test_app.test_cli_runner()
