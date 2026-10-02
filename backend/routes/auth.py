from flask import Blueprint, jsonify, request, session
from flask_wtf.csrf import generate_csrf
from backend import db
from backend.models.user import User
import backend.services.auth_service as auth_service
from backend.utils.validation_helpers import DuplicateAccountError

auth_bp = Blueprint('auth', __name__)

def api_error(code, message, status):
    return jsonify({"error": {"code": code, "message": message}}), status


def json_payload(required_fields):
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return None, api_error("invalid_json", "Expected a JSON object.", 400)

    if any(not isinstance(data.get(field), str) for field in required_fields):
        return None, api_error("invalid_fields", "All required fields must be strings.", 400)

    return data, None


@auth_bp.get('/api/auth/csrf')
def get_csrf_token():
    response = jsonify({"csrf_token": generate_csrf()})
    response.headers["Cache-Control"] = "no-store"
    return response


@auth_bp.route('/api/auth/register', methods=['POST'])
def register():
    data, error_response = json_payload(("username", "email", "password", "confirm_password"))
    if error_response:
        return error_response

    try:
        user = auth_service.register_user(
            username=data["username"],
            email=data["email"].strip().lower(),
            password=data["password"],
            confirm_password=data["confirm_password"]
        )
    except DuplicateAccountError as error:
        return api_error("account_exists", str(error), 409)
    except ValueError as error:
        return api_error("validation_error", str(error), 400)

    return jsonify({
        "user": {
            "id": user.id,
            "username": user.username,
            "email": user.email,
        }
    }), 201


@auth_bp.post('/api/auth/login')
def login():
    data, error_response = json_payload(("email", "password"))
    if error_response:
        return error_response

    try:
        user = auth_service.login_user(
            email=data["email"],
            password=data["password"]
        )
    except ValueError:
        return api_error("invalid_credentials", "Invalid email or password.", 401)

    session.clear()
    session['user_id'] = user.id
    session['username'] = user.username

    return jsonify({
        "user": {
            "id": user.id,
            "username": user.username,
            "email": user.email,
        }
    }), 200


@auth_bp.post('/api/auth/logout')
def logout():
    """Clear the active user session."""
    session.clear()
    return "", 204

@auth_bp.get('/api/auth/me')
def get_current_user():
    user_id = session.get('user_id')
    if user_id is None:
        return api_error("unauthenticated", "Not authenticated.", 401)

    user = db.session.get(User, user_id)
    if not user:
        session.clear()
        return api_error("unauthenticated", "Not authenticated.", 401)

    return jsonify({
        "user": {
            "id": user.id,
            "username": user.username,
            "email": user.email,
        }
    }), 200
