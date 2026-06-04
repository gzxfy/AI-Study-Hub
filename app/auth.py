from flask import Blueprint, render_template, redirect, request, session, url_for, flash, current_app
from werkzeug.security import generate_password_hash, check_password_hash
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
        username = (request.form.get('username') or '').strip()
        email = (request.form.get('email') or '').strip().lower()
        password = request.form.get('password') or ''
        confirm_password = request.form.get('confirm_password') or ''

        try:
            if not username:
                raise ValueError('Username is required.')

            # validate input
            validation_helpers.validate_email_and_password(email, password)
            if password != confirm_password:
                raise ValueError('Passwords do not match.')

            if User.query.filter_by(email=email).first():
                raise ValueError('Email already registered. Please use a different email or log in.')
            if User.query.filter_by(username=username).first():
                raise ValueError('Username already taken. Please choose a different username.')

            password_hash = generate_password_hash(password)
            new_user = User(username=username, email=email, password_hash=password_hash)

            db.session.add(new_user)
            db.session.commit()

            flash("Registration successful! Please log in.", "success")
            return redirect(url_for('auth.login'))

        except ValueError as ve:
            flash(str(ve), "danger")
            password = ''  # Clear password field on error
            confirm_password = ''  # Clear confirm password field on error
        except Exception:
            db.session.rollback()
            current_app.logger.exception('Registration failed with an unexpected error')
            flash('An unexpected error occurred. Please try again later.', 'danger')
            password = ''  # Clear password field on error
            confirm_password = ''  # Clear confirm password field on error
            email = ''  # Clear email field on error
    return render_template('register.html', email=email, password=password, confirm_password=confirm_password, error=error, success=success)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    success = None
    email = None
    password = None

    if request.method == 'POST':
        email = (request.form.get('email') or '').strip().lower()
        password = request.form.get('password') or ''

        try:
            if not email:
                raise ValueError('Email is required.')
            if not password:
                raise ValueError('Password is required.')

            validation_helpers.validate_email_and_password(email, password)

            user = User.query.filter_by(email=email).first()
            if not user or not check_password_hash(user.password_hash, password):
                raise ValueError('Invalid email or password.')
            
            session.clear()
            session['user_id'] = user.id
            session['username'] = user.username
            flash('Login successful! Welcome back.', 'success')
            return redirect(url_for('main.home'))

        except ValueError as ve:
            flash(str(ve), "danger")
            password = ''  # Clear password field on error
        except Exception:
            current_app.logger.exception('Login failed with an unexpected error')
            flash('An unexpected error occurred. Please try again later.', 'danger')
            password = ''  # Clear password field on error
            email = ''  # Clear email field on error
    return render_template('login.html', email=email, password=password, error=error, success=success)


@auth_bp.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('username', None)
    flash('You have been logged out.', 'success')
    return redirect(url_for('main.home'))
