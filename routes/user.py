from flask import Blueprint, render_template, request, redirect, url_for, flash, abort
from flask_login import login_required, current_user
from functools import wraps
from models import db, Trek, Booking
from werkzeug.security import generate_password_hash

user_bp = Blueprint('user', __name__)


def user_required(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'user':
            abort(403)
        return func(*args, **kwargs)
    return wrapper


@user_bp.route('/dashboard')
@login_required
@user_required
def dashboard():
    available_treks = Trek.query.filter(Trek.status.in_(['Approved', 'Open'])).limit(5).all()
    my_bookings_list = Booking.query.filter_by(user_id=current_user.id).order_by(Booking.booking_date.desc()).limit(5).all()
    return render_template(
        'user/dashboard.html',
        available_treks=available_treks,
        my_bookings=my_bookings_list,
        active_page='dashboard'
    )


@user_bp.route('/treks')
@login_required
@user_required
def browse_treks():
    query = Trek.query.filter(Trek.status.in_(['Approved', 'Open']))

    difficulty = request.args.get('difficulty')
    location = request.args.get('location')

    if difficulty:
        query = query.filter_by(difficulty=difficulty)
    if location:
        query = query.filter(Trek.location.ilike(f'%{location}%'))

    treks = query.all()
    return render_template('user/browse_treks.html', treks=treks, active_page='browse')


@user_bp.route('/treks/<int:trek_id>/book', methods=['POST'])
@login_required
@user_required
def book_trek(trek_id):
    trek = Trek.query.get_or_404(trek_id)

    if trek.status != 'Open':
        flash('This trek is not open for booking.', 'danger')
        return redirect(url_for('user.browse_treks'))

    if trek.available_slots <= 0:
        flash('Sorry, this trek is fully booked.', 'danger')
        return redirect(url_for('user.browse_treks'))

    already_booked = Booking.query.filter_by(user_id=current_user.id, trek_id=trek.id, status='Booked').first()
    if already_booked:
        flash('You have already booked this trek.', 'warning')
        return redirect(url_for('user.browse_treks'))

    new_booking = Booking(user_id=current_user.id, trek_id=trek.id, status='Booked')
    trek.available_slots -= 1
    db.session.add(new_booking)
    db.session.commit()

    flash(f'Successfully booked {trek.name}!', 'success')
    return redirect(url_for('user.my_bookings'))


@user_bp.route('/bookings')
@login_required
@user_required
def my_bookings():
    bookings = Booking.query.filter_by(user_id=current_user.id).order_by(Booking.booking_date.desc()).all()
    return render_template('user/bookings.html', bookings=bookings, active_page='bookings')


@user_bp.route('/bookings/<int:booking_id>/cancel', methods=['POST'])
@login_required
@user_required
def cancel_booking(booking_id):
    booking = Booking.query.get_or_404(booking_id)

    if booking.user_id != current_user.id:
        abort(403)

    if booking.status == 'Booked':
        booking.status = 'Cancelled'
        booking.trek.available_slots += 1
        db.session.commit()
        flash('Booking cancelled.', 'info')
    else:
        flash('This booking cannot be cancelled.', 'warning')

    return redirect(url_for('user.my_bookings'))


@user_bp.route('/history')
@login_required
@user_required
def history():
    completed = Booking.query.filter_by(user_id=current_user.id, status='Completed').order_by(Booking.booking_date.desc()).all()
    return render_template('user/history.html', bookings=completed, active_page='history')


@user_bp.route('/profile', methods=['GET', 'POST'])
@login_required
@user_required
def profile():
    if request.method == 'POST':
        current_user.name = request.form.get('name')
        current_user.contact = request.form.get('contact')

        new_password = request.form.get('new_password')
        if new_password:
            current_user.password = generate_password_hash(new_password)

        db.session.commit()
        flash('Profile updated.', 'success')
        return redirect(url_for('user.profile'))

    return render_template('user/profile.html', active_page='profile')
@user_bp.route('/treks/<int:trek_id>')
@login_required
@user_required
def trek_details(trek_id):
    trek = Trek.query.get_or_404(trek_id)
    already_booked = Booking.query.filter_by(user_id=current_user.id, trek_id=trek.id, status='Booked').first()
    return render_template('user/trek_details.html', trek=trek, already_booked=already_booked, active_page='browse')