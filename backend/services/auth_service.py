from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.exc import IntegrityError
from backend import db
from backend.models.models import User
import backend.utils.validation_helpers as validation_helpers

def register_user(username, email, password, confirm_password):
    """Validate registration details, hash the password, and create a user."""
    username = username.strip()
    email = email.strip().lower()

    validation_helpers.validate_user_data_for_registration(username, email, password, confirm_password)
    validation_helpers.validate_if_username_or_email_exists(username, email)

    hashed_password = generate_password_hash(password)
    new_user = User(username=username, email=email, password_hash=hashed_password)
    db.session.add(new_user)
    try:
        db.session.commit()
    except IntegrityError as error:
        db.session.rollback()
        raise validation_helpers.DuplicateAccountError(
            "Username or email is already registered."
        ) from error
    return new_user

def login_user(email, password):
    """Validate credentials and return the matching authenticated user."""
    if not isinstance(email, str) or not isinstance(password, str):
        raise ValueError("Invalid email or password.")

    email = email.strip().lower()
    validation_helpers.validate_email(email)

    user = User.query.filter_by(email=email).first()
    if not user or not check_password_hash(user.password_hash, password):
        raise ValueError("Invalid email or password.")
    
    return user