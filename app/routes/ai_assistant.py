from flask import flash, redirect, url_for, render_template, request, session, Blueprint
from app.models.models import Conversation, Note, Message, db
from app.utils.validation_helpers import login_required
from app import csrf
from app.services.ai_service import ask_ai, ask_ai_with_topics


ai_assistant_bp = Blueprint('ai_assistant', __name__)

@ai_assistant_bp.route('/chat/<int:note_id>', methods=['GET', 'POST'])
@csrf.exempt  # Exempt the AI assistant route from CSRF protection
@login_required  # Ensure the user is logged in before accessing the AI assistant route
def ai_assistant(note_id):
    note = Note.query.filter_by(id=note_id, user_id=session.get("user_id")).first()

    try:
        if not note:
            raise ValueError("Note not found or you do not have permission to access it.")
    except ValueError as ve:
        flash(str(ve), 'danger')
        return redirect(url_for('main.home'))
    
    conversation = note.conversation if note.conversation else None
    if not conversation:
        conversation = Conversation(note_id=note_id, user_id=session.get("user_id"))
        db.session.add(conversation)
        db.session.commit()

    messages = conversation.messages
    if request.method == 'POST':
        question = (request.form.get('message') or '').strip()

        if question:
            prior_messages = Message.query.filter_by(conversation_id=conversation.id).order_by(Message.timestamp.asc()).all()
            ai_response = ask_ai(question, note.content, prior_messages)

            db.session.add(Message(conversation_id=conversation.id, role='user', content=question))
            db.session.add(Message(conversation_id=conversation.id, role='assistant', content=ai_response))
            db.session.commit()
            
        return redirect(url_for('ai_assistant.ai_assistant', note_id=note_id))
    return render_template('AI_Assistant.html', note=note, messages=messages)

@ai_assistant_bp.route('/chat/topics/<int:note_id>', methods=['POST', 'GET'])
@csrf.exempt
@login_required
def ai_assistant_with_topics(note_id):
    note = Note.query.filter_by(id=note_id, user_id=session.get("user_id")).first()

    if not note:
        flash("Note not found or you do not have permission to access it.", "danger")
        return redirect(url_for('main.home'))
    
    topic_notes = []
    if note.topic_id:
        topic_notes = Note.query.filter_by(
            user_id=session.get("user_id"),
            topic_id=note.topic_id
        ).all()

    conversation = note.conversation if note.conversation else None
    if not conversation:
        conversation = Conversation(note_id=note_id, user_id=session.get("user_id"))
        db.session.add(conversation)
        db.session.commit()
    
    messages = conversation.messages

    if request.method == 'POST':
        question = (request.form.get('message') or '').strip()

        if question:
            prior_messages = Message.query.filter_by(conversation_id=conversation.id).order_by(Message.timestamp.asc()).all()
            ai_response = ask_ai_with_topics(session.get("user_id"), question, topic_notes, prior_messages)
            
            db.session.add(Message(conversation_id=conversation.id, role='user', content=question))
            db.session.add(Message(conversation_id=conversation.id, role='assistant', content=ai_response))
            db.session.commit()

        return redirect(url_for('ai_assistant.ai_assistant_with_topics', note_id=note_id))
    return render_template('AI_Assistant.html', note=note, messages=messages)