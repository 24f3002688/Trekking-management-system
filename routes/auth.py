from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, User

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        role = request.form.get('role')  # 'staff' or 'user'
        contact = request.form.get('contact')

        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash('Email already registered. Please login.', 'danger')
            return redirect(url_for('auth.register'))

        # Staff must be approved by admin before their dashboard works;
        # Users are active immediately
        status = 'pending' if role == 'staff' else 'active'

        new_user = User(
            name=name,
            email=email,
            password=generate_password_hash(password),
            role=role,
            contact=contact,
            status=status
        )
        db.session.add(new_user)
        db.session.commit()

        flash('Registration successful! Please login.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('auth/register.html')


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        user = User.query.filter_by(email=email).first()

        if not user or not check_password_hash(user.password, password):
            flash('Invalid email or password.', 'danger')
            return redirect(url_for('auth.login'))

        if user.role == 'staff' and user.status == 'pending':
            flash('Your account is awaiting admin approval.', 'warning')
            return redirect(url_for('auth.login'))

        if user.status == 'blacklisted':
            flash('Your account has been blacklisted. Contact admin.', 'danger')
            return redirect(url_for('auth.login'))

        login_user(user)
        flash(f'Welcome back, {user.name}!', 'success')

        if user.role == 'admin':
            return redirect(url_for('admin.dashboard'))  # placeholder until admin dashboard exists
        elif user.role == 'staff':
            return redirect(url_for('staff.dashboard'))  # placeholder until staff dashboard exists
        else:
            return redirect(url_for('user.dashboard'))  # placeholder until user dashboard exists

    return render_template('auth/login.html')


@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('auth.login'))