from flask import flash, redirect, url_for, render_template, request, session, Blueprint
from app.utils.validation_helpers import login_required
import app.services.flashcard_service as flashcard_service
from app import csrf

flashcard_bp = Blueprint('flashcard', __name__)

@flashcard_bp.route('/createFlashcard', methods=['GET', 'POST'])
@csrf.exempt
@login_required
def create_flashcard():
    user_id = session.get('user_id')  # Get the logged-in user's ID
    topic_id = request.form.get('topic_id')
    if not topic_id:
        topic_id = None  # Set a default value or handle the case where no topic_id is provided
    if request.method == 'POST':
        try:
            flashcard_service.create_flashcard(
                user_id=user_id,
                topic_id=topic_id,
                note_id=request.form.get('note_id'),
                question=request.form.get('question', ''),
                answer=request.form.get('answer', ''),
                difficulty=request.form.get('difficulty', '')
            )
            flash('Flashcard created successfully!', 'success')
            return redirect(url_for('main.home'))
        except ValueError as ve:
            flash(str(ve), 'danger')
    return render_template('create_flashcard.html', note_id=request.form.get('note_id', ''), topic_id=topic_id, question=request.form.get('question', ''), answer=request.form.get('answer', ''), difficulty=request.form.get('difficulty', '' ))  # Render the flashcard creation template
