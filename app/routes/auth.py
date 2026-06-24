from flask import Blueprint, render_template, redirect, request, session, url_for, flash, current_app
from ..models.models import User, db
import app.services.auth_service as auth_service

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    email = ""
    username = ""
    if request.method == 'POST':
        try:
            auth_service.register_user(
                username=request.form.get('username') or '',
                email=(request.form.get('email') or '').strip().lower(),
                password=request.form.get('password') or '',
                confirm_password=request.form.get('confirm_password') or ''
            )
            flash("Registration successful! Please log in.", "success")
            return redirect(url_for('auth.login'))

        except ValueError as ve:
            flash(str(ve), "danger")

        # except Exception:
        #     db.session.rollback()
        #     current_app.logger.exception('Registration failed with an unexpected error')
        #     flash('An unexpected error occurred. Please try again later.', 'danger')

    return render_template('register.html', username=username, email=email)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    email = ""
    password = ""
    
    if request.method == 'POST':
        try:
            user = auth_service.login_user(
                email=(request.form.get('email') or '').strip().lower(),
                password=request.form.get('password') or ''
            )
            
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
    return render_template('login.html', email=email, password=password)


@auth_bp.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('username', None)
    flash('You have been logged out.', 'success')
    return redirect(url_for('main.home'))
