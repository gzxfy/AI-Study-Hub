from flask import flash, redirect, render_template, Blueprint, request, session, url_for

import validation_helpers
from .models import Note, db

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def home():
    return render_template('home.html')

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

        try:
            validation_helpers.validate_note_data(title, content)
        except ValueError as ve:
            flash(str(ve), 'danger')
            return render_template('create_note.html', content=content, title=title)  # Render the create page with existing data on error
        

        new_note = Note(user_id=user_id, title=title, content=content)
        db.session.add(new_note)
        db.session.commit()
        flash('Note created successfully!')  # Add a flash message to indicate successful creation
        return redirect(url_for('main.home'))
    return render_template('create_note.html', content=content, title=title)  # Render the create page for GET requests

@main_bp.route('/view/<int:note_id>')
def view_note(note_id):
    note = Note.query.get(note_id)
    if not note:
        flash('Note not found!', 'danger')
        return redirect(url_for('main.home'))
    return render_template('view_note.html', note=note)
    
