from flask import Blueprint, flash, jsonify, request, session
import app.utils.validation_helpers as validation_helpers
from app.services import study_mode_service, progress_service
from app import csrf


study_mode_bp = Blueprint('study_mode', __name__) 

@study_mode_bp.route('/study_mode/start', methods=['GET'])
@csrf.exempt
@validation_helpers.login_required
def start_study_mode():
    user_id = session.get('user_id')  
    try:
        note_id = int(request.args.get('note_id'))  
        card_count_raw = request.args.get('card_count')  
        card_count = int(card_count_raw) if card_count_raw else None
    except (TypeError, ValueError):
        return jsonify({"error": "Invalid parameters, must be positive integers"}), 400  
    difficulty = request.args.get('difficulty')  
    priority = request.args.get('priority')  

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

@study_mode_bp.route('/study_mode/end', methods=['POST'])
@csrf.exempt
@validation_helpers.login_required
def end_study_mode():
    user_id = session.get('user_id')  
    payload = request.get_json() or {} 
    reviewed_results = payload.get('reviewed_results', []) 

    summary = study_mode_service.end_study_mode(user_id=user_id, reviewed_results=reviewed_results)
    return jsonify(summary)  