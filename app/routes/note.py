from flask import flash, redirect, url_for, render_template, request, session, Blueprint
from app.models.models import Note, Topic
import app.utils.validation_helpers as validation_helpers
from app.utils.validation_helpers import login_required
import app.services.note_service as note_service
from app import csrf

note_bp = Blueprint('note', __name__)

@note_bp.route('/create_note', methods=['GET', 'POST'])
@csrf.exempt  # Exempt the create route from CSRF protection
@login_required  # Ensure the user is logged in before accessing the create route
def create_note():
    user_id = session.get("user_id")  # Retrieve the user_id from the session
    topics = Topic.query.filter_by(user_id=user_id).all()

    if request.method == 'POST':
        topic_id = request.form.get('topic_id')  # Get the topic_id from the form, if provided
        if not topic_id:
            topic_id = None  # Set topic_id to None if not provided
        print("User ID:", user_id)  # Debugging: Print the user_id
        try:
            note_service.create_note(
                user_id=user_id, 
                title=request.form.get('title', ''), 
                content=request.form.get('content', ''), 
                topic_id=topic_id
                )
            flash('Note created successfully!', 'success')
            return redirect(url_for('main.home'))
        except ValueError as ve:
            flash(str(ve), 'danger')
    return render_template('create_note.html', content=request.form.get('content', ''), title=request.form.get('title', ''), topic_id=request.form.get('topic_id'), topics=topics)  # Render the create page with existing data on error


@note_bp.route('/view/<int:note_id>', methods=['GET'])
@csrf.exempt  # Exempt the view route from CSRF protection
@login_required  # Ensure the user is logged in before accessing the view note route
def view_note(note_id):

    try:
        note = note_service.view_note(note_id, session.get("user_id"))
    except ValueError as ve:
        flash(str(ve), 'danger')
        return redirect(url_for('main.home'))
    
    return render_template('view_note.html', note=note)

@note_bp.route('/delete_note/<int:note_id>')
@csrf.exempt  # Exempt the delete route from CSRF protection
@login_required  # Ensure the user is logged in before accessing the delete note route
def delete_note(note_id):
    
    try:
        note_service.delete_note(note_id, session.get("user_id"))
        flash('Note deleted successfully!', 'success')
    except ValueError as ve:
        flash(str(ve), 'danger')
    return redirect(url_for('main.home'))

@note_bp.route('/edit_note/<int:note_id>', methods=['GET', 'POST'])
@csrf.exempt  # Exempt the edit route from CSRF protection
@login_required  # Ensure the user is logged in before accessing the edit route
def edit_note(note_id):
    if request.method == 'POST':
        try:
            new_note = note_service.edit_note(
                note_id=note_id,
                user_id=session.get("user_id"),
                title=request.form.get('title', ''),
                content=request.form.get('content', '')
            )
            flash('Note updated successfully!', 'success')
            return redirect(url_for('note.view_note', note_id=new_note.id))
        except ValueError as ve:
            flash(str(ve), 'danger')
    return render_template('edit_note.html', note=Note.query.get(note_id))  # Render the edit page for GET requests