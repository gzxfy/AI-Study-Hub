from flask import Blueprint, jsonify, request, session
import app.utils.validation_helpers as validation_helpers
from app.services import quiz_service
from app import csrf

quiz_mode_bp = Blueprint('quiz_mode', __name__)

def require_int(value, name):
    if value is None:
        raise ValueError(f"{name} is required and must be a positive integer")
    try:
        return int(value)
    except (TypeError, ValueError):
        raise ValueError(f"Invalid {name}, must be a positive integer")
    

@quiz_mode_bp.route('/quiz/start', methods=['POST'])
@csrf.exempt
@validation_helpers.login_required
def start_quiz():
    data = request.get_json() or {}
    try:
        note_id = require_int(data.get('note_id', None), 'note_id')
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    topic_id_raw = data.get("topic_id")
    topic_id = int(topic_id_raw) if topic_id_raw not in (None, "") else None    
    question_count = data.get('question_count', 10)
    difficulty = data.get('difficulty')

    user_id = session['user_id']
    try:
        quiz_attempt, questions = quiz_service.start_quiz(user_id=user_id, 
                                                          note_id=note_id, 
                                                          topic_id=topic_id,
                                                          question_count=question_count,
                                                          difficulty=difficulty)
        return jsonify({
            "quiz_attempt_id": quiz_attempt.id,
            "status": quiz_attempt.status,
            "question_index": quiz_attempt.question_index,
            "questions": [
                {
                    "id": q.id,
                    "question": q.question,
                    "difficulty": q.difficulty
                } for q in questions
            ]
        }), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    
# This route is for getting the current question in an ongoing quiz attempt.
@quiz_mode_bp.route('/quiz/current', methods=['GET'])
@csrf.exempt
@validation_helpers.login_required
def get_current_quiz_question():
    quiz_attempt_id = require_int(request.args.get('quiz_attempt_id'), 'quiz_attempt_id')
    user_id = session['user_id']
    try:
        quiz_attempt = quiz_service.get_quiz_attempt_for_user(quiz_attempt_id, user_id)
        question = quiz_service.get_current_quiz_question(user_id, quiz_attempt)
        if question is None:
            return jsonify({
                "quiz_attempt_id": quiz_attempt_id,
                "status": "completed",
                "message": "Quiz completed, no more questions.",    
                "question": None
            }), 200
        return jsonify({
            "quiz_attempt_id": quiz_attempt_id,
            "status": quiz_attempt.status,
            "question_index": quiz_attempt.question_index,
            "question": {
                "id": question.id,
                "question": question.question,
                "difficulty": question.difficulty
            }
        })
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    
    
@quiz_mode_bp.route('/quiz/submit_answer', methods=['POST'])
@csrf.exempt
@validation_helpers.login_required
def submit_quiz_answer():
    data = request.get_json() or {}
    quiz_attempt_id = require_int(data.get('quiz_attempt_id'), 'quiz_attempt_id')
    flashcard_id = require_int(data.get('flashcard_id'), 'flashcard_id')
    user_answer = data.get('user_answer')
    time_taken = float(data.get('time_taken', 0))

    user_id = session['user_id']
    try:
        result = quiz_service.submit_quiz_answer(user_id, quiz_attempt_id, flashcard_id, user_answer, time_taken)
        quiz_attempt = quiz_service.get_quiz_attempt_for_user(quiz_attempt_id, user_id)
        next_question_obj = quiz_service.get_current_quiz_question(user_id, quiz_attempt)
        next_question = {
            "id": next_question_obj.id,
            "question": next_question_obj.question,
            "difficulty": next_question_obj.difficulty
        } if next_question_obj else None
        return jsonify({
            "quiz_attempt_id": result["quiz_attempt_id"],
            "flashcard_id": result["flashcard_id"],
            "is_correct": result["is_correct"],
            "correct_answer": result["correct_answer"],
            "score": result["score"],
            "question_index": result["question_index"],
            "status": result["status"],
            "next_question": next_question,
        }), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    

@quiz_mode_bp.route('/quiz/finish', methods=['POST'])
@csrf.exempt
@validation_helpers.login_required
def finish_quiz():
    data = request.get_json()
    quiz_attempt_id = require_int(data.get('quiz_attempt_id'), 'quiz_attempt_id')

    user_id = session['user_id']
    try:
        summary = quiz_service.finish_quiz(user_id, quiz_attempt_id)
        return jsonify(summary), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    
    
@quiz_mode_bp.route('/quiz/review/question', methods=['GET'])
@csrf.exempt
@validation_helpers.login_required
def review_quiz_question():
    quiz_attempt_id = require_int(request.args.get('quiz_attempt_id'), 'quiz_attempt_id')
    flashcard_id = require_int(request.args.get('flashcard_id'), 'flashcard_id')
    ask_ai = request.args.get('ask_ai', 'false').lower() == 'true'
    feedback = request.args.get('feedback', '')
    user_id = session['user_id']
    try:
        review = quiz_service.review_quiz_question(user_id, quiz_attempt_id, flashcard_id, feedback=feedback, ask_ai=ask_ai)
        return jsonify(review), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    
    
@quiz_mode_bp.route('/quiz/review/summary', methods=['GET'])
@csrf.exempt
@validation_helpers.login_required
def review_quiz_summary():
    quiz_attempt_id = require_int(request.args.get('quiz_attempt_id'), 'quiz_attempt_id')
    ask_ai = request.args.get('ask_ai', 'false').lower() == 'true'
    feedback = request.args.get('feedback', '')
    user_id = session['user_id']
    try:
        summary = quiz_service.get_quiz_review_summary(user_id, quiz_attempt_id, ask_ai=ask_ai, feedback=feedback)
        return jsonify(summary), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 400