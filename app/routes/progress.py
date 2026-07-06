from flask import flash, redirect, url_for, render_template, request, session, Blueprint
from app.utils.validation_helpers import login_required
from app import csrf
import app.services.progress_service as progress_service

progress_bp = Blueprint('progress', __name__)

@progress_bp.route('/progress')
@login_required
def progress_dashboard():
    user_id = session.get('user_id')
    progress = progress_service.get_user_progress(user_id)
    return render_template('progress_dashboard.html', progress=progress)

@progress_bp.route('/user_progress')
@login_required
def user_progress():
    user_id = session.get('user_id')
    progress = progress_service.get_user_progress(user_id)
    return render_template('progress_dashboard.html', progress=progress)