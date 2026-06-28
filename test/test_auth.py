from flask import app
import pytest

from app.models.models import User
import app.services.auth_service as auth_service
# =====REGISTER TESTS=====
def test_register_form_includes_csrf_token(client):
    response = client.get('/register')
    assert response.status_code == 200
    assert b'name="csrf_token"' in response.data


def test_register(test_app):
    with test_app.app_context():
        user = auth_service.register_user(
            username='testuser',
            email='testuser@example.com',
            password='TestPassword1!',
            confirm_password='TestPassword1!'
        )
        user = User.query.filter_by(email='testuser@example.com').first()
        assert user is not None
        assert user.email == 'testuser@example.com'
        assert user.username == 'testuser'
        assert user.password_hash is not None
        assert user.password_hash != 'TestPassword1!'  # Ensure the password is hashed

def test_mismatched_passwords(test_app):
    with test_app.app_context():
        with pytest.raises(ValueError) as excinfo:
            auth_service.register_user(
                username='testuser2',
                email='testuser2@example.com',
                password='TestPassword1!',
                confirm_password='WrongPassword1!'
            )
        assert str(excinfo.value) == "Passwords do not match."  # Ensure the correct error message is raised
        assert 'testuser2@example.com' not in [user.email for user in User.query.all()]  # Ensure the user was not created
        

def test_duplicate_email(test_app):
    with test_app.app_context():
            auth_service.register_user(
                username='testuser3',
                email='testuser3@example.com',
                password='TestPassword1!',
                confirm_password='TestPassword1!'
            )
            with pytest.raises(ValueError) as excinfo:
                auth_service.register_user(
                    username='testuser4',
                    email='testuser3@example.com',
                    password='TestPassword1!',
                    confirm_password='TestPassword1!'
                )
            assert str(excinfo.value) == "Email already registered."  # Ensure the correct error message is raised
            assert 'testuser3@example.com' in [user.email for user in User.query.all()]  # Ensure the original user was created


# =====LOGIN TESTS=====
def test_login_form_includes_csrf_token(client):
    response = client.get('/login')
    assert response.status_code == 200
    assert b'name="csrf_token"' in response.data


def test_login(client):
    # First, register a user to log in with
    client.post('/register', data={
        'username': 'loginuser',
        'email': 'loginuser@example.com',
        'password': 'TestPassword1!',
        'confirm_password': 'TestPassword1!'
    }, follow_redirects=True)

    response = client.post('/login', data={
        'email': 'loginuser@example.com',
        'password': 'TestPassword1!'
    }, follow_redirects=True)

    assert response.status_code == 200
    assert b'Login successful! Welcome back.' in response.data

def test_invalid_login(client):
    client.post('/register', data={
        'username': 'testuser',
        'email': 'loginuser@example.com',
        'password': 'TestPassword1!',
        'confirm_password': 'TestPassword1!'
    }, follow_redirects=True)

    response = client.post('/login', data={
        'email': 'testuser@example.com',
        'password': 'WrongPassword1!'
    }, follow_redirects=True)

    assert response.status_code == 200
    assert b'Invalid email or password.' in response.data

def test_empty_email_login(client):
    response = client.post('/login', data={
        'email': '',
        'password': 'TestPassword1!'
    }, follow_redirects=True)

    assert response.status_code == 200
    assert b'Email is required.' in response.data

def test_empty_password_login(client):
    response = client.post('/login', data={
        'email': 'testuser@example.com',
        'password': ''
    }, follow_redirects=True)

    assert response.status_code == 200
    assert b'Invalid email or password.' in response.data
