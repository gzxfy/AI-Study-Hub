from flask import Blueprint, render_template, redirect, request, url_for, flash
from werkzeug.security import generate_password_hash
from .models import User, db
import validation_helpers

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    username = None
    error = None
    success = None
    email = None
    password = None
    confirm_password = None
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')

        try:
            # validate input 
            validation_helpers.validate_email_and_password(email, password)
            if password != confirm_password:
                raise ValueError("Passwords do not match.")
            
            existing_user = User.query.filter_by(email=email).first()
            if existing_user:
                raise ValueError("Email already registered. Please use a different email or log in.")
            
            password_hash = generate_password_hash(password)
            new_user = User(username=username, email=email, password_hash=password_hash)

            db.session.add(new_user)
            db.session.commit()

            flash("Registration successful! Please log in.", "success")
            return redirect(url_for('auth.register'))

        except ValueError as ve:
            flash(str(ve), "danger")
            password = ''  # Clear password field on error
            confirm_password = ''  # Clear confirm password field on error
        except Exception as e:
            db.session.rollback()
            flash(f"An error occurred: {e}", "danger")
            password = ''  # Clear password field on error
            confirm_password = ''  # Clear confirm password field on error
            email = ''  # Clear email field on error
    return render_template('register.html', email=email, password=password, confirm_password=confirm_password, error=error, success=success)