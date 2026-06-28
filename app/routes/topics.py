from flask import flash, redirect, url_for, render_template, request, session, Blueprint

from app import db
from app.models.models import User, Conversation, Note, Topic, db, Message
from app.utils.validation_helpers import login_required
from app import csrf
import app.services.topic_service as topic_service
topic_bp = Blueprint('topic', __name__)

@topic_bp.route('/topic/create', methods=['GET', 'POST'])
@csrf.exempt  # Exempt the topic create route from CSRF protection
@login_required  # Ensure the user is logged in before accessing the topic create route
def topic_create():
    user_id = session.get("user_id")  # Retrieve the user_id from the session
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        color = request.form.get('color')

        try:
            topic_service.create_topic(user_id, title, description, color)
            flash('Topic created successfully!', 'success')
            return redirect(url_for('main.home'))
        except ValueError as ve:
            flash(str(ve), 'danger')
    return render_template('create_topic.html', title=request.form.get('title', ''), description=request.form.get('description', ''), color=request.form.get('color', ''))  # Render the create topic page with existing data on error or empty fields for GET requests

@topic_bp.route('/delete_topic/<int:topic_id>')
@csrf.exempt  # Exempt the create route from CSRF protection
@login_required  # Ensure the user is logged in before accessing the delete topic route
def delete_topic(topic_id):
    try:
        topic_service.delete_topic(topic_id, session.get("user_id"))
        flash('Topic deleted successfully!', 'success')
    except ValueError as ve:
        flash(str(ve), 'danger')
    return redirect(url_for('main.home'))


@topic_bp.route('/edit_topic/<int:topic_id>', methods=['GET', 'POST'])
@csrf.exempt  # Exempt the edit note route from CSRF protection
@login_required  # Ensure the user is logged in before accessing the edit note route
def edit_topic(topic_id):
    if request.method == 'POST':
        try:
            topic_service.edit_topic(
                topic_id=topic_id,
                user_id=session.get("user_id"),
                title=request.form.get('title', ''),
                description=request.form.get('description', ''),
                color=request.form.get('color', '')
            )
            flash('Topic updated successfully!', 'success')
            return redirect(url_for('main.home'))
        except ValueError as ve:
            flash(str(ve), 'danger')
            return render_template('edit_topic.html', topic=Topic.query.get(topic_id))  # Render the edit topic page with existing data on error
    topic = Topic.query.get_or_404(topic_id)
    return render_template('edit_topic.html', topic=topic)  # Render the edit topic page for GET requests



@topic_bp.route('/topic/<int:topic_id>')
@csrf.exempt  # Exempt the topic view route from CSRF protection
@login_required  # Ensure the user is logged in before accessing the topic view route
def topic_view(topic_id):
    try:
        topic = topic_service.topic_view(topic_id, session.get("user_id"))
        notes = Note.query.filter_by(topic_id=topic_id).all()  # Fetch all notes associated with the topic
    except ValueError as ve:
        flash(str(ve), 'danger')
        return redirect(url_for('main.home'))
    return render_template('view_topic.html', topic=topic, notes=notes)  # Render the view topic page with associated notes