from flask import Blueprint, flash, jsonify, request, session
from app.models.models import StudyPlanDay
import app.utils.validation_helpers as validation_helpers
from app.services import study_plan_service, progress_service
from app import csrf
from datetime import datetime, timedelta

study_plan_bp = Blueprint('study_plan', __name__)

@study_plan_bp.route('/study_plan/generate', methods=['POST'])
@csrf.exempt
@validation_helpers.login_required
def generate_study_plan():
    user_id = session.get('user_id')  # Get the logged-in user's ID
    payload = request.get_json() or {}  # Get the JSON payload from the request
    days_until_exam = payload.get('days_until_exam', 7)  # Default to 7 days if not provided
    start_date_str = payload.get('start_date')  # Optional start date in string format

    # Validate days_until_exam
    if not isinstance(days_until_exam, int) or days_until_exam <= 0:
        return jsonify({"error": "days_until_exam must be a positive integer."}), 400

    # Convert start_date_str to a datetime object if provided
    start_date = None
    if start_date_str:
        try:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
        except ValueError:
            return jsonify({"error": "start_date must be in YYYY-MM-DD format."}), 400

    try:
        study_plan_service.generate_and_save_study_plan(user_id, days_until_exam=days_until_exam, start_date=start_date)
        return jsonify({"message": "Study plan generated successfully."}), 200
    except ValueError as ve:
        return jsonify({"error": str(ve)}), 400
    except Exception:
        return jsonify({"error": "An unexpected error occurred while generating the study plan."}), 500
    
@study_plan_bp.route('/study_plan/current', methods=['GET'])
@csrf.exempt
@validation_helpers.login_required
def get_current_study_plan():
    user_id = session.get("user_id")
    plan = study_plan_service.get_current_study_plan(user_id)
    if not plan:
        return jsonify({"error": "No active study plan found."}), 404

    days = StudyPlanDay.query.filter_by(study_plan_id=plan.id).order_by(StudyPlanDay.day_number.asc()).all()
    return jsonify({
    "id": plan.id,
    "title": plan.title,
    "start_date": plan.start_date.isoformat(),
    "end_date": plan.end_date.isoformat(),
    "status": plan.status,
    "days": [
        {
        "day_number": d.day_number,
        "date": d.date.date().isoformat(),
        "task_json": d.task_json,
        "estimated_time_minutes": d.estimated_time_minutes,
        "completed": d.completed
        }
        for d in days
        ]
    }), 200

@study_plan_bp.route('/study_plan/day/complete', methods=['POST'])
@csrf.exempt
@validation_helpers.login_required
def complete_study_plan_day():
    user_id = session.get('user_id')
    payload = request.get_json() or {}
    day_number = payload.get('day_number')

    # Validate day_number
    if not isinstance(day_number, int) or day_number <= 0:
        return jsonify({"error": "day_number must be a positive integer."}), 400

    try:
        progress_summary = study_plan_service.complete_study_plan_day(user_id, day_number)
        return jsonify(progress_summary), 200
    except ValueError as ve:
        return jsonify({"error": str(ve)}), 400
    except Exception:
        return jsonify({"error": "An unexpected error occurred while completing the study plan day."}), 500
    

@study_plan_bp.route('/study_plan/delete', methods=['GET'])
@csrf.exempt
@validation_helpers.login_required
def delete_study_plan():
    user_id = session.get('user_id')
    study_plan_id = request.args.get('study_plan_id')  # Optional: specify a study plan ID to delete
    try:
        study_plan_service.delete_study_plan(user_id, study_plan_id=study_plan_id)  # Assuming we delete the current active plan
        return jsonify({"message": "Study plan deleted successfully."}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
@study_plan_bp.route('/study_plan/progress', methods=['GET'])
@csrf.exempt
@validation_helpers.login_required
def get_study_plan_progress():
    user_id = session.get('user_id')
    study_plan_id = request.args.get('study_plan_id')  # Optional: specify a study plan ID to get progress for
    try:
        progress = study_plan_service.get_study_plan_progress(user_id, study_plan_id=study_plan_id)
        return jsonify(progress), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500