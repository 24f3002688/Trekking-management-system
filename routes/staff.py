from flask import Blueprint, render_template, request, redirect, url_for, flash, abort
from flask_login import login_required, current_user
from functools import wraps
from models import db, Trek, Booking

staff_bp = Blueprint('staff', __name__)


def staff_required(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'staff':
            abort(403)
        if current_user.status != 'approved':
            abort(403)
        return func(*args, **kwargs)
    return wrapper


@staff_bp.route('/dashboard')
@login_required
@staff_required
def dashboard():
    assigned_treks = Trek.query.filter_by(assigned_staff_id=current_user.id).all()

    total_participants = 0
    open_treks = 0
    for trek in assigned_treks:
        total_participants += Booking.query.filter_by(trek_id=trek.id, status='Booked').count()
        if trek.status == 'Open':
            open_treks += 1

    return render_template(
        'staff/dashboard.html',
        assigned_treks=assigned_treks,
        total_participants=total_participants,
        open_treks=open_treks,
        active_page='dashboard'
    )


@staff_bp.route('/treks')
@login_required
@staff_required
def my_treks():
    assigned_treks = Trek.query.filter_by(assigned_staff_id=current_user.id).all()
    return render_template('staff/treks.html', assigned_treks=assigned_treks, active_page='treks')


@staff_bp.route('/treks/<int:trek_id>', methods=['GET', 'POST'])
@login_required
@staff_required
def manage_trek(trek_id):
    trek = Trek.query.get_or_404(trek_id)

    if trek.assigned_staff_id != current_user.id:
        abort(403)

    if request.method == 'POST':
        action = request.form.get('action')

        if action == 'update':
            new_available = int(request.form.get('available_slots'))
            trek.available_slots = min(new_available, trek.total_slots)
            trek.status = request.form.get('status')
            db.session.commit()
            flash('Trek updated.', 'success')

        elif action == 'mark_started':
            trek.status = 'Open'
            db.session.commit()
            flash('Trek marked as started (Open).', 'success')

        elif action == 'mark_completed':
            trek.status = 'Completed'
            for booking in trek.bookings:
                if booking.status == 'Booked':
                    booking.status = 'Completed'
            db.session.commit()
            flash('Trek marked as completed. All bookings updated.', 'success')

        return redirect(url_for('staff.manage_trek', trek_id=trek.id))

    participants = [b for b in trek.bookings if b.status in ('Booked', 'Completed')]
    return render_template('staff/manage_trek.html', trek=trek, participants=participants, active_page='treks')