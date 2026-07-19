from functools import wraps
import re

from flask import flash, session, redirect, url_for
from app.models.models import User

# Validation helper functions for email and password
def validate_email(email):
    if email is None or email.strip() == "":
        raise ValueError("Email is required.")
    
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(pattern, email):
        raise ValueError("Invalid email format.")
    
def validate_username(username):
    if username is None or username.strip() == "":
        raise ValueError("Username is required.")
    if len(username) < 3:
        raise ValueError("Username must be at least 3 characters long.")
    if len(username) > 50:
        raise ValueError("Username cannot be longer than 50 characters.")
    return True
    
def validate_password(password):
    if password is None or password.strip() == "":
        raise ValueError("Password is required.")
    if len(password) < 8:
        raise ValueError("Password must be at least 8 characters long.")
    if not re.search(r'[A-Z]', password):
        raise ValueError("Password must contain at least one uppercase letter.")
    if not re.search(r'[a-z]', password):
        raise ValueError("Password must contain at least one lowercase letter.")
    if not re.search(r'[0-9]', password):
        raise ValueError("Password must contain at least one digit.")
    if not re.search(r"[!@#$%^&*()\-_=+\[\]{}|;:'\",.<>?/\\`~]", password):
        raise ValueError("Password must contain at least one special character.")
    return True

def validate_email_and_password(email, password):
    validate_email(email)
    validate_password(password)
    return True

def validate_user_data_for_registration(username, email, password, confirm_password):
    username = (username or "").strip()
    email = (email or "").strip()
    validate_username(username)
    validate_email(email)
    validate_password(password)
    if password != confirm_password:
        raise ValueError("Passwords do not match.")
    return True

def validate_user_data_for_login(email, password):
    email = (email or "").strip()
    validate_email(email)
    validate_password(password)
    return True

def validate_if_username_or_email_exists(username, email):
    username = (username or "").strip()
    email = (email or "").strip()
    if User.query.filter_by(username=username).first():
        raise ValueError("Username is already taken.")
    
    if User.query.filter_by(email=email).first():
        raise ValueError("Email already registered.")
    
    return True

# Will most likely be changed to use a more robust validation library in the future, and for better error handling and user feedback, but this is a simple validation function for now.
def validate_item_data(title, description, price, url):
    if not title or not description or price in (None, '') or not url:
        raise ValueError("Title, description, price, and picture URL are required.")
    try:
        price_float = float(price)
    except (ValueError, TypeError):
        raise ValueError("Price must be a valid number.")
    if price_float < 0:
        raise ValueError("Price must be a positive number.")
    return True

# Validation helper function for notes
def validate_note_data(title, content):
    if not title or title.strip() == "":
        raise ValueError("Title is required.")
    if not content or content.strip() == "":
        raise ValueError("Content is required.")
    if len(title) > 100:
        raise ValueError("Title cannot be longer than 100 characters.")
    if len(content) > 5000:
        raise ValueError("Content cannot be longer than 5000 characters.")
    # Additional validation can be added here, such as checking for prohibited words or formatting requirements
    return True

# Validation helper function for topics
def validate_topic_data(title, description, color):
    if not title or title.strip() == "":
        raise ValueError("Title is required.")
    if not description or description.strip() == "":
        raise ValueError("Description is required.")
    if not color or color.strip() == "":
        color = "#000000"  # Default color if none is provided
    if len(title) > 100:
        raise ValueError("Title cannot be longer than 100 characters.")
    if len(description) > 1000:
        raise ValueError("Description cannot be longer than 1000 characters.")
    # Additional validation can be added here, such as checking for prohibited words or formatting requirements
    return True

def validate_flashcard_data(question, answer, difficulty=None):
    if not question or question.strip() == "":
        raise ValueError("Question is required.")
    if not answer or answer.strip() == "":
        raise ValueError("Answer is required.")
    if difficulty and difficulty not in ('easy', 'medium', 'hard'):
        raise ValueError("Difficulty must be 'easy', 'medium', or 'hard' if provided.")
    if len(question) > 500:
        raise ValueError("Question cannot be longer than 500 characters.")
    if len(answer) > 2000:
        raise ValueError("Answer cannot be longer than 2000 characters.")
    return True

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash("You must be logged in to access this page.", "danger")
            return redirect(url_for('auth.login'))  # Redirect to login page if user is not logged in
        return f(*args, **kwargs)
    return decorated_function


# Validation helper functions for study sessions and quizzes

VALID_DIFFICULTIES = ['easy', 'medium', 'hard']

def validate_study_difficulty(difficulty=None, card_count=None):
    if difficulty and difficulty not in VALID_DIFFICULTIES:
        raise ValueError(f"Invalid difficulty level. Valid options are: {', '.join(VALID_DIFFICULTIES)}")
    if card_count is not None:
        if not isinstance(card_count, int) or card_count <= 0:
            raise ValueError("card_count must be a positive integer")
    return True

def validate_quiz_difficulty(difficulty=None, question_count=None):
    if difficulty and difficulty not in VALID_DIFFICULTIES:
        raise ValueError(f"Invalid difficulty level. Valid options are: {', '.join(VALID_DIFFICULTIES)}")
    if question_count is not None:
        if not isinstance(question_count, int) or question_count <= 0:
            raise ValueError("question_count must be a positive integer")
    return True


def validate_study_event_data(user_id, flashcard_id, is_correct, source=None):
    if not isinstance(user_id, int) or user_id <= 0:
        raise ValueError("user_id must be a positive integer.")
    if not isinstance(flashcard_id, int) or flashcard_id <= 0:
        raise ValueError("flashcard_id must be a positive integer.")
    if not isinstance(is_correct, bool):
        raise ValueError("is_correct must be a boolean value.")
    if source is not None and not isinstance(source, str):
        raise ValueError("source must be a string if provided.")
    return True