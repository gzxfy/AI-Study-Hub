from werkzeug.security import generate_password_hash
from app import db
from app.models.models import User
import app.utils.validation_helpers as validation_helpers

def register_user(username, email, password, confirm_password):
    print("ENTERING THE FUNCTION register_user")
    #basic validation
    validation_helpers.validate_user_data(username, email, password, confirm_password)
    print("VALIDATION PASSED")
    #check if the username or email already exists in the database
    validation_helpers.validate_if_username_or_email_exists(username, email)
    print("USERNAME AND EMAIL VALIDATION PASSED")
    #hash the password
    hashed_password = generate_password_hash(password)
    print("PASSWORD HASHING PASSED")
    #create a new user instance
    new_user = User(username=username, email=email, password_hash=hashed_password)
    print("USER CREATION PASSED")
    #add the new user to the database
    db.session.add(new_user)
    db.session.commit()
    print("EXITING THE FUNCTION register_user")
    return new_user