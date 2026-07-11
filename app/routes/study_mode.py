from flask import Blueprint, flash, jsonify, request, session
import app.utils.validation_helpers as validation_helpers
from app.services import study_mode_service, progress_service
from app import csrf


study_mode_bp = Blueprint('study_mode', __name__) 

@study_mode_bp.route('/study_mode/start', methods=['GET'])
@csrf.exempt
@validation_helpers.login_required
def start_study_mode():

    user_id = session.get('user_id')  # Get the logged-in user's ID
    note_id = request.args.get('note_id')  # Assuming the note_id is passed as a query parameter
    difficulty = request.args.get('difficulty')  # Assuming the difficulty is passed as a query parameter
    card_count_raw = request.args.get('card_count')  # Assuming the card_count is passed as a query parameter
    card_count = int(card_count_raw) if card_count_raw else None
    priority = request.args.get('priority')  # Assuming the priority is passed as a query parameter

    cards = study_mode_service.start_study_mode(user_id=user_id, note_id=note_id, difficulty=difficulty, card_count=card_count, priority=priority)

    return jsonify([
        {"id": card.id, "question": card.question, "answer": card.answer, "difficulty": card.difficulty} for card in cards
        ])  # Return the flashcards as JSON response

@study_mode_bp.route('/study_mode/review', methods=['POST'])
@csrf.exempt
@validation_helpers.login_required
def review_study_mode():
    user_id = session.get('user_id')  # Get the logged-in user's ID
    payload = request.get_json() or {}  # Get the JSON payload from the request
    flashcard_id = payload.get('flashcard_id')  # Get the flashcard_id from the payload
    marked_correctly = payload.get('marked_correctly')  # Get the marked_correctly
    review = study_mode_service.review_flashcard(user_id=user_id, flashcard_id=flashcard_id, marked_correctly=marked_correctly)
    return jsonify({
        "flashcard_id": review.flashcard_id,
        "times_seen": review.times_seen,
        "times_correct": review.times_correct,
        "streak": review.streak,
        "progress": review.progress
    })
    # user_id = session.get('user_id')  # Get the logged-in user's ID
    # if request.method == 'GET':
    #     try:
    #         note_id = request.args.get('note_id')  # Assuming the note_id is passed as a query parameter
    #         difficulty = request.args.get('difficulty')  # Assuming the difficulty is passed as a query parameter
    #         card_count = request.args.get('card_count')  # Assuming the card_count is passed as a query parameter
    #         priority = request.args.get('priority')  # Assuming the priority is passed as a query parameter
    #         flash("Study mode review started successfully!", "success")
    #         return study_mode_service.review_flashcard(user_id=user_id, note_id=note_id, difficulty=difficulty, card_count=card_count, priority=priority)
    #     except ValueError as ve:
    #         return str(ve), 400
    return '', 405  # Method not allowed if not GET

@study_mode_bp.route('/study_mode/end', methods=['POST'])
@csrf.exempt
@validation_helpers.login_required
def end_study_mode():
    user_id = session.get('user_id')  # Get the logged-in user's ID
    payload = request.get_json() or {}  # Get the JSON payload from the request
    reviewed_results = payload.get('review_results', [])  # Get the review results from the payload

    summary = study_mode_service.end_study_mode(user_id=user_id, reviewed_results=reviewed_results)
    return jsonify(summary)  # Return the summary of the study session as JSON response