from mailbox import Message
from pyexpat.errors import messages

from flask import flash, redirect, render_template, Blueprint, request, session, url_for
from flask_wtf import csrf

from app.services.ai_service import ask_ai
import validation_helpers
from .models import Conversation, Note, Topic, db, Message

main_bp = Blueprint('main', __name__)


@main_bp.route('/')
def home():
    user_id = session.get("user_id")  # Get the user_id from the session
    notes = Note.query.filter_by(user_id=user_id).all()  # Get all notes for the logged-in user

    recent_notes = sorted(notes, key=lambda x: x.id, reverse=True)[:5]  # Get the 5 most recent notes
    return render_template('home.html', notes=notes, recent_notes=recent_notes, note_count=len(notes))

# will add topics later
@main_bp.route('/create', methods=['GET', 'POST'])
def create():
    content = None  # Initialize content variable or any other logic needed before rendering the create page
    title = None  # Initialize title variable or any other logic needed before rendering the create page

    if request.method == 'POST':
        # Add logic to handle form submission or data processing
        user_id = session.get("user_id")  # Retrieve the user_id from the session
        if not user_id:
            flash('User not logged in!')
            return redirect(url_for('main.home'))
        
        content = request.form.get('content', '')
        title = request.form.get('title', '')
        topic_id = request.form.get('topic_id')  # Get the topic_id from the form, if provided
        if not topic_id:
            topic_id = None  # Convert the topic_id to an integer if provided

        try:
            validation_helpers.validate_note_data(title, content)
        except ValueError as ve:
            flash(str(ve), 'danger')
            return render_template('create_note.html', content=content, title=title)  # Render the create page with existing data on error
        

        new_note = Note(user_id=user_id, title=title, content=content, topic_id=topic_id)
        db.session.add(new_note)
        db.session.commit()
        flash('Note created successfully!')  # Add a flash message to indicate successful creation
        return redirect(url_for('main.home'))
    return render_template('create_note.html', content=content, title=title, topic_id=None)  # Render the create page for GET requests

@main_bp.route('/view/<int:note_id>', methods=['GET'])
def view_note(note_id):
    note = Note.query.get(note_id)

    if not note:
        flash('Note not found!', 'danger')
        return redirect(url_for('main.home'))
    
    if note.user_id != session.get("user_id"):
        flash('You do not have permission to view this note!', 'danger')
        return redirect(url_for('main.home'))
    
    return render_template('view_note.html', note=note)

@main_bp.route('/delete/<int:note_id>')
def delete_note(note_id):
    note = Note.query.get(note_id)
    if not note:
        flash('Note not found!', 'danger')
        return redirect(url_for('main.home'))
    if note.user_id != session.get("user_id"):
        flash('You do not have permission to delete this note!', 'danger')
        return redirect(url_for('main.home'))
    db.session.delete(note)
    db.session.commit()
    flash('Note deleted successfully!', 'success')
    return redirect(url_for('main.home'))

@main_bp.route('/edit/<int:note_id>', methods=['GET', 'POST'])
def edit_note(note_id):
    note = Note.query.get(note_id)

    if not note:
        flash('Note not found!', 'danger')
        return redirect(url_for('main.home'))
    
    if note.user_id != session.get("user_id"):
        flash('You do not have permission to edit this note!', 'danger')
        return redirect(url_for('main.home'))
    
    if request.method == 'POST':
        title = request.form.get('title')
        content = request.form.get('content')
        try:
            validation_helpers.validate_note_data(title, content)
        except ValueError as ve:
            flash(str(ve), 'danger')
            return render_template('edit_note.html', note=note)  # Render the edit page with existing data on error
        
        note.title = title
        note.content = content
        db.session.commit()
        flash('Note updated successfully!', 'success')
        return redirect(url_for('main.view_note', note_id=note.id))
    return render_template('edit_note.html', note=note)  # Render the edit page for GET requests

@main_bp.route('/topic/create', methods=['GET', 'POST'])
def topic_create():
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        color = request.form.get('color')

        try:
            validation_helpers.validate_topic_data(title, description, color)
        except ValueError as ve:
            flash(str(ve), 'danger')
            return render_template('create_topic.html', title=title, description=description, color=color)  # Render the create topic page with existing data on error
        new_topic = Topic(
            user_id=session.get("user_id"),
            title=title,
            description=description,
            color=color
        )
        db.session.add(new_topic)
        db.session.commit()
        flash('Topic created successfully!', 'success')
        return redirect(url_for('main.home'))
    return render_template('create_topic.html')  # Render the create topic page for GET requests

@main_bp.route('/topic/<int:topic_id>')
def topic_view(topic_id):
    topic = Topic.query.get_or_404(topic_id)
    if topic.user_id != session.get("user_id"):
        flash('You do not have permission to view this topic!', 'danger')
        return redirect(url_for('main.home'))
    # Retrieve the notes associated with this topic
    notes = Note.query.filter_by(topic_id=topic.id).all()
    return render_template('view_topic.html', topic=topic, notes=notes)  # Render the view topic page with associated notes

#inspired and made with the help of ChatGPT
@main_bp.route('/search')
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
        print("POST request received")
        question = request.form.get('message').strip()

        if question:
            user_message = Message(conversation_id=conversation.id, role='user', content=question)
            db.session.add(user_message)
            ai_response = ask_ai(question, note_content=note.content)
            assistant_message = Message(conversation_id=conversation.id, role='assistant', content=ai_response)
            db.session.add(assistant_message)
            db.session.commit()
            
        return redirect(url_for('main.ai_assistant', note_id=note_id))
    return render_template('AI Assistant.html', note=note, messages=messages)

# @main_bp.route('/debug-notes')
# def debug_notes():

#     notes = Note.query.all()

#     return {
#         "count": len(notes),
#         "notes": [
#             {
#                 "id": note.id,
#                 "user_id": note.user_id,
#                 "title": note.title
#             }
#             for note in notes
#         ]
#     }

# @main_bp.route('/debug-session')
# def debug_session():
#     return {
#         "user_id": session.get("user_id"),
#         "username": session.get("username")
#     }



# @main_bp.route('/debug-ai', methods=['GET', 'POST'])
# @csrf.exempt
# def debug_ai():
    
#     answer = None

#     if request.method == 'POST':
#         question = request.form.get('message')

#         answer = ask_ai(
#             question,
#             note_content="Binary search repeatedly divides a sorted array."
#         )

#     return render_template(
#         'debug_ai.html',
#         answer=answer
#     )

# @main_bp.route('/debug-ai', methods=['GET', 'POST'])
# @csrf.exempt
# def create():
#     content = None  # Initialize content variable or any other logic needed before rendering the create page
#     title = None  # Initialize title variable or any other logic needed before rendering the create page

#     if request.method == 'POST':
#     # Add logic to handle form submission or data processing
#         user_id = session.get("user_id")  # Retrieve the user_id from the session
#         if not user_id:
#             flash('User not logged in!')
#             return redirect(url_for('main.home'))
        
#         content = request.form.get('content', '')
#         title = request.form.get('title', '')
#         topic_id = request.form.get('topic_id')  # Get the topic_id from the form, if provided
#         if not topic_id:
#             topic_id = None  # Convert the topic_id to an integer if provided

#         try:
#             validation_helpers.validate_note_data(title, content)
#         except ValueError as ve:
#             flash(str(ve), 'danger')
#             return render_template('create_note.html', content=content, title=title)  # Render the create page with existing data on error
        

#         new_note = Note(user_id=user_id, title=title, content=content, topic_id=topic_id)
#         db.session.add(new_note)
#         db.session.commit()
#         flash('Note created successfully!')  # Add a flash message to indicate successful creation
#         return redirect(url_for('main.home'))
#     return render_template('create_note.html', content=content, title=title)  # Render the create page for GET requests