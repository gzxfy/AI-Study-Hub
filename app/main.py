from mailbox import Message
from pydoc_data.topics import topics
from pyexpat.errors import messages

from flask import flash, redirect, render_template, Blueprint, request, session, url_for

from app.services.ai_service import ask_ai
import app.utils.validation_helpers as validation_helpers
from app.utils.validation_helpers import login_required
from .models.models import Conversation, Note, Topic, db, Message
from . import csrf

main_bp = Blueprint('main', __name__)


@main_bp.route('/')
def home():
    user_id = session.get("user_id")  # Get the user_id from the session
    notes = Note.query.filter_by(user_id=user_id).all()  # Get all notes for the logged-in user

    recent_notes = sorted(notes, key=lambda x: x.id, reverse=True)[:5]  # Get the 5 most recent notes
    return render_template('home.html', notes=notes, recent_notes=recent_notes, note_count=len(notes))




#inspired and made with the help of ChatGPT
@main_bp.route('/search')
@csrf.exempt  # Exempt the search route from CSRF protection
@login_required  # Ensure the user is logged in before accessing the search route
def search():
    search_query = request.args.get('q', '').strip()
    search_type = request.args.get('type', 'all').strip()

    note_results = []
    topic_results = []

    if search_type == 'notes':
        note_results = Note.query.filter(
            Note.user_id == session.get("user_id"),
            (
                Note.title.contains(search_query)
                |
                Note.content.contains(search_query)
            )
        ).all()

    elif search_type == 'topics':
        topic_results = Topic.query.filter(
            Topic.user_id == session.get("user_id"),
            Topic.title.contains(search_query)
        ).all()

    else:
        note_results = Note.query.filter(
            Note.user_id == session.get("user_id"),
            (
                Note.title.contains(search_query)
                |
                Note.content.contains(search_query)
            )
        ).all()

        topic_results = Topic.query.filter(
            Topic.user_id == session.get("user_id"),
            Topic.title.contains(search_query)
        ).all()

    return render_template(
        'search.html',
        note_results=note_results,
        topic_results=topic_results,
        search_query=search_query,
        search_type=search_type
    )

