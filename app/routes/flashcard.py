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


@flashcard_bp.route('/flashcard/<int:flashcard_id>', methods=['GET'])
@login_required
def view_flashcard(flashcard_id):
    user_id = session.get('user_id')  # Get the logged-in user's ID
    flashcard = flashcard_service.get_flashcard_by_id(flashcard_id, user_id=user_id)
    if not flashcard or flashcard.user_id != user_id:
        flash('Flashcard not found.', 'danger')
        return redirect(url_for('main.home'))
    return render_template('view_flashcard.html', flashcard=flashcard)

@flashcard_bp.route('/flashcards', methods=['GET'])
@login_required
def view_all_flashcards():
    user_id = session.get('user_id')  # Get the logged-in user's ID
    flashcards = flashcard_service.get_all_flashcards(user_id)  # Get flashcards only for the logged-in user
    return render_template('view_all_flashcards.html', flashcards=flashcards)

@flashcard_bp.route('/editFlashcard/<int:flashcard_id>', methods=['GET', 'POST'])
@csrf.exempt
@login_required
def edit_flashcard(flashcard_id):
    user_id = session.get('user_id')  # Get the logged-in user's ID
    flashcard = flashcard_service.get_flashcard_by_id(flashcard_id, user_id=user_id)
    if not flashcard or flashcard.user_id != user_id:
        flash('Flashcard not found.', 'danger')
        return redirect(url_for('main.home'))
    if request.method == 'POST':
        try:
            flashcard_service.edit_flashcard(
                flashcard_id=flashcard_id,
                user_id=user_id,
                question=request.form.get('question', ''),
                answer=request.form.get('answer', ''),
                difficulty=request.form.get('difficulty', '')
            )
            flash('Flashcard updated successfully!', 'success')
            return redirect(url_for('flashcard.view_flashcard', flashcard_id=flashcard_id))
        except ValueError as ve:
            flash(str(ve), 'danger')
    return render_template('edit_flashcard.html', flashcard=flashcard)


@flashcard_bp.route('/deleteFlashcard/<int:flashcard_id>', methods=['POST'])
@csrf.exempt
@login_required
def delete_flashcard(flashcard_id):
    user_id = session.get('user_id')  # Get the logged-in user's ID
    try:
        flashcard_service.delete_flashcard(flashcard_id, user_id)
        flash('Flashcard deleted successfully!', 'success')
    except ValueError as ve:
        flash(str(ve), 'danger')
    return redirect(url_for('main.home'))

