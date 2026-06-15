from flask import flash, redirect, render_template, Blueprint, request, session, url_for
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
        

        new_note = Note(user_id=user_id, title=title, content=content)
        db.session.add(new_note)
        db.session.commit()
        flash('Note created successfully!')  # Add a flash message to indicate successful creation
        return redirect(url_for('main.home'))
    return render_template('create.html', content=content, title=title)  # Render the create page for GET requests
    
