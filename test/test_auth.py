from werkzeug.security import generate_password_hash

from backend import db
from backend.models.user import User
import backend.services.auth_service as auth_service


PASSWORD = "TestPassword1!"


def register(client, username="testuser", email="testuser@example.com", password=PASSWORD):
    return client.post("/api/auth/register", json={
        "username": username,
        "email": email,
        "password": password,
        "confirm_password": password,
    })


def test_register_creates_user_and_returns_public_user(client, test_app):
    response = register(client, email=" TESTUSER@EXAMPLE.COM ")

    assert response.status_code == 201
    assert response.json["user"] == {
        "id": 1,
        "username": "testuser",
        "email": "testuser@example.com",
    }
    assert "password" not in response.json["user"]

    with test_app.app_context():
        user = User.query.filter_by(email="testuser@example.com").one()
        assert user.password_hash != PASSWORD
        assert auth_service.login_user(user.email, PASSWORD).id == user.id


def test_register_rejects_mismatched_passwords(client):
    response = client.post("/api/auth/register", json={
        "username": "testuser",
        "email": "testuser@example.com",
        "password": PASSWORD,
        "confirm_password": "DifferentPassword1!",
    })

    assert response.status_code == 400
    assert response.json["error"]["code"] == "validation_error"
    assert response.json["error"]["message"] == "Passwords do not match."


def test_register_rejects_duplicate_email(client):
    assert register(client).status_code == 201

    response = register(client, username="anotheruser", email="testuser@example.com")

    assert response.status_code == 409
    assert response.json["error"]["code"] == "account_exists"


def test_register_rejects_non_json_and_missing_fields(client):
    non_json_response = client.post("/api/auth/register", data="not json")
    missing_field_response = client.post("/api/auth/register", json={"email": "user@example.com"})

    assert non_json_response.status_code == 400
    assert non_json_response.json["error"]["code"] == "invalid_json"
    assert missing_field_response.status_code == 400
    assert missing_field_response.json["error"]["code"] == "invalid_fields"


def test_login_establishes_session_used_by_current_user_endpoint(client):
    assert register(client).status_code == 201

    response = client.post("/api/auth/login", json={
        "email": " TESTUSER@EXAMPLE.COM ",
        "password": PASSWORD,
    })

    assert response.status_code == 200
    assert response.json["user"]["username"] == "testuser"

    current_user_response = client.get("/api/auth/me")
    assert current_user_response.status_code == 200
    assert current_user_response.json["user"] == response.json["user"]


def test_login_preserves_password_whitespace(client):
    password = "TestPassword1! "
    assert register(client, password=password).status_code == 201

    valid_password_response = client.post("/api/auth/login", json={
        "email": "testuser@example.com",
        "password": password,
    })
    trimmed_password_response = client.post("/api/auth/login", json={
        "email": "testuser@example.com",
        "password": password.strip(),
    })

    assert valid_password_response.status_code == 200
    assert trimmed_password_response.status_code == 401


def test_login_does_not_reapply_registration_password_policy(client, test_app):
    with test_app.app_context():
        user = User(
            username="legacyuser",
            email="legacy@example.com",
            password_hash=generate_password_hash("legacy"),
        )
        db.session.add(user)
        db.session.commit()

    response = client.post("/api/auth/login", json={
        "email": "legacy@example.com",
        "password": "legacy",
    })

    assert response.status_code == 200
    assert response.json["user"]["username"] == "legacyuser"


def test_login_failure_is_generic_and_does_not_authenticate(client):
    assert register(client).status_code == 201

    response = client.post("/api/auth/login", json={
        "email": "testuser@example.com",
        "password": "WrongPassword1!",
    })

    assert response.status_code == 401
    assert response.json["error"] == {
        "code": "invalid_credentials",
        "message": "Invalid email or password.",
    }
    assert client.get("/api/auth/me").status_code == 401


def test_login_rejects_missing_fields_without_server_error(client):
    response = client.post("/api/auth/login", json={"email": "user@example.com"})

    assert response.status_code == 400
    assert response.json["error"]["code"] == "invalid_fields"


def test_logout_clears_session_and_requires_post(client):
    assert register(client).status_code == 201
    assert client.post("/api/auth/login", json={
        "email": "testuser@example.com",
        "password": PASSWORD,
    }).status_code == 200

    response = client.post("/api/auth/logout")

    assert response.status_code == 204
    assert client.get("/api/auth/me").status_code == 401
    assert client.get("/api/auth/logout").status_code == 405


def test_api_csrf_token_is_required_when_csrf_is_enabled(client, test_app):
    test_app.config["WTF_CSRF_ENABLED"] = True
    token_response = client.get("/api/auth/csrf")
    assert token_response.status_code == 200
    assert token_response.headers["Cache-Control"] == "no-store"

    missing_token_response = register(client)
    assert missing_token_response.status_code == 400
    assert missing_token_response.json["error"]["code"] == "csrf_failed"

    valid_token_response = client.post(
        "/api/auth/register",
        json={
            "username": "csrfuser",
            "email": "csrf@example.com",
            "password": PASSWORD,
            "confirm_password": PASSWORD,
        },
        headers={"X-CSRFToken": token_response.json["csrf_token"]},
    )
    assert valid_token_response.status_code == 201
