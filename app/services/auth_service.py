from werkzeug.security import generate_password_hash, check_password_hash
from app import db
from app.models.models import User
import app.utils.validation_helpers as validation_helpers

def register_user(username, email, password, confirm_password):
    #basic validation
    validation_helpers.validate_user_data_for_registration(username, email, password, confirm_password)

    #check if the username or email already exists in the database
    validation_helpers.validate_if_username_or_email_exists(username, email)

    #hash the password
    hashed_password = generate_password_hash(password)

    #create a new user instance
    new_user = User(username=username, email=email, password_hash=hashed_password)

    #add the new user to the database
    db.session.add(new_user)
    db.session.commit()
    return new_user

def login_user(email, password):
    #basic validation
    validation_helpers.validate_email(email)

    #check if the user exists in the database
    user = User.query.filter_by(email=email).first()
    if not user or not check_password_hash(user.password_hash, password):
        raise ValueError("Invalid email or password.")
    
    return user