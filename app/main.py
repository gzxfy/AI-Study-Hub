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


@main_bp.route('/chat/<int:note_id>', methods=['GET', 'POST'])
@csrf.exempt  # Exempt the AI assistant route from CSRF protection
@login_required  # Ensure the user is logged in before accessing the AI assistant route
def ai_assistant(note_id):
    note = Note.query.filter_by(id=note_id, user_id=session.get("user_id")).first()

    if not note:
        flash("Note not found.", "error")
        return redirect(url_for('main.home'))
    
    conversation = note.conversation if note.conversation else None
    if not conversation:
        conversation = Conversation(note_id=note_id, user_id=session.get("user_id"))
        db.session.add(conversation)
        db.session.commit()

    messages = conversation.messages
    if request.method == 'POST':
        question = request.form.get('message').strip()

        if question:
            user_message = Message(
                conversation_id=conversation.id, 
                role='user',
                content=question
            )

            db.session.add(user_message)
            db.session.flush()

            conversation_messages = Message.query.filter_by(conversation_id=conversation.id).order_by(Message.timestamp.asc()).all()

            ai_response = ask_ai(question=question, note_content=note.content, conversation_messages=conversation_messages)
            assistant_message = Message(conversation_id=conversation.id, role='assistant', content=ai_response)
            
            db.session.add(assistant_message)
            db.session.commit()
            
        return redirect(url_for('main.ai_assistant', note_id=note_id))
    return render_template('AI_Assistant.html', note=note, messages=messages)

