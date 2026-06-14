from flask import flash, render_template, Blueprint, request
from .models import Note, db

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def home():
    return render_template('home.html')

@main_bp.route('/create', methods=['GET', 'POST'])
def create():
    content = None  # Initialize content variable or any other logic needed before rendering the create page
    title = None  # Initialize title variable or any other logic needed before rendering the create page

    if request.method == 'POST':
        # Add logic to handle form submission or data processing
        content = request.form.get('content', '')
        title = request.form.get('title', '')

        new_note = Note(title=title, content=content)
        db.session.add(new_note)
        db.session.commit()
    

    flash('Note created successfully!')  # Add a flash message to indicate successful creation
    return render_template('home.html', content=content, title=title)