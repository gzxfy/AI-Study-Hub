from flask import Blueprint, current_app, jsonify, render_template, session
from backend.utils.validation_helpers import login_required
from backend import db
from backend.models.models import User
import backend.services.progress_service as progress_service

progress_bp = Blueprint('progress', __name__)


def api_json(data, status=200):
    response = jsonify(data)
    response.headers["Cache-Control"] = "no-store"
    return response, status


def api_error(code, message, status):
    return api_json({"error": {"code": code, "message": message}}, status)


@progress_bp.get('/api/progress')
def api_user_progress():
    """Return the signed-in user's supported study progress summary."""
    user_id = session.get("user_id")
    if not isinstance(user_id, int) or isinstance(user_id, bool):
        session.clear()
        return api_error("unauthenticated", "Not authenticated.", 401)

    try:
        if db.session.get(User, user_id) is None:
            session.clear()
            return api_error("unauthenticated", "Not authenticated.", 401)
        progress = progress_service.get_user_progress(user_id)
    except Exception:
        db.session.rollback()
        current_app.logger.exception("Progress API request failed.")
        return api_error("internal_error", "Unable to load study progress.", 500)

    return api_json({"progress": progress})

@progress_bp.route('/progress')
@login_required
def progress_dashboard():
    """Render the signed-in user's flashcard study progress dashboard."""
    user_id = session.get('user_id')
    progress = progress_service.get_user_progress(user_id)
    return render_template('progress_dashboard.html', progress=progress)

@progress_bp.route('/user_progress')
@login_required
def user_progress():
    """Render the same progress summary through the legacy progress route."""
    user_id = session.get('user_id')
    progress = progress_service.get_user_progress(user_id)
    return render_template('progress_dashboard.html', progress=progress)