from flask import Blueprint, render_template
from flask_login import login_required, current_user
from models import db, User, Trek, Booking
from flask import request, redirect, url_for, flash
from datetime import datetime

admin_bp = Blueprint('admin', __name__)


def admin_required(func):
    """Simple check: only allow access if logged-in user is an admin."""
    from functools import wraps
    from flask import abort

    @wraps(func)
    def wrapper(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'admin':
            abort(403)
        return func(*args, **kwargs)
    return wrapper


@admin_bp.route('/dashboard')
@login_required
@admin_required
def dashboard():
    total_treks = Trek.query.count()
    total_users = User.query.filter_by(role='user').count()
    total_staff = User.query.filter_by(role='staff').count()
    total_bookings = Booking.query.count()

    recent_bookings = Booking.query.order_by(Booking.booking_date.desc()).limit(5).all()

    return render_template(
        'admin/dashboard.html',
        total_treks=total_treks,
        total_users=total_users,
        total_staff=total_staff,
        total_bookings=total_bookings,
        recent_bookings=recent_bookings,
        active_page='dashboard'
    )
@admin_bp.route('/treks')
@login_required
@admin_required
def manage_treks():
    search = request.args.get('search', '')
    if search:
        treks = Trek.query.filter(Trek.name.ilike(f'%{search}%')).all()
    else:
        treks = Trek.query.all()
    return render_template('admin/treks.html', treks=treks, active_page='treks')


@admin_bp.route('/treks/add', methods=['GET', 'POST'])
@login_required
@admin_required
def add_trek():
    staff_list = User.query.filter_by(role='staff', status='approved').all()

    if request.method == 'POST':
        name = request.form.get('name')
        location = request.form.get('location')
        difficulty = request.form.get('difficulty')
        duration = request.form.get('duration')
        total_slots = request.form.get('total_slots')
        assigned_staff_id = request.form.get('assigned_staff_id') or None
        start_date = request.form.get('start_date')
        end_date = request.form.get('end_date')
        description = request.form.get('description')

        new_trek = Trek(
            name=name,
            location=location,
            difficulty=difficulty,
            duration=int(duration),
            total_slots=int(total_slots),
            available_slots=int(total_slots),
            assigned_staff_id=int(assigned_staff_id) if assigned_staff_id else None,
            status='Pending',
            start_date=datetime.strptime(start_date, '%Y-%m-%d').date(),
            end_date=datetime.strptime(end_date, '%Y-%m-%d').date(),
            description=description
        )
        db.session.add(new_trek)
        db.session.commit()

        flash('Trek added successfully!', 'success')
        return redirect(url_for('admin.manage_treks'))

    return render_template('admin/add_edit_trek.html', staff_list=staff_list, trek=None, active_page='treks')


@admin_bp.route('/treks/edit/<int:trek_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_trek(trek_id):
    trek = Trek.query.get_or_404(trek_id)
    staff_list = User.query.filter_by(role='staff', status='approved').all()

    if request.method == 'POST':
        trek.name = request.form.get('name')
        trek.location = request.form.get('location')
        trek.difficulty = request.form.get('difficulty')
        trek.duration = int(request.form.get('duration'))

        new_total = int(request.form.get('total_slots'))
        # Keep booked count consistent when admin changes total slots
        booked_count = trek.total_slots - trek.available_slots
        trek.total_slots = new_total
        trek.available_slots = max(new_total - booked_count, 0)

        assigned_staff_id = request.form.get('assigned_staff_id') or None
        trek.assigned_staff_id = int(assigned_staff_id) if assigned_staff_id else None
        trek.status = request.form.get('status')
        trek.start_date = datetime.strptime(request.form.get('start_date'), '%Y-%m-%d').date()
        trek.end_date = datetime.strptime(request.form.get('end_date'), '%Y-%m-%d').date()
        trek.description = request.form.get('description')

        db.session.commit()
        flash('Trek updated successfully!', 'success')
        return redirect(url_for('admin.manage_treks'))

    return render_template('admin/add_edit_trek.html', staff_list=staff_list, trek=trek, active_page='treks')


@admin_bp.route('/treks/delete/<int:trek_id>', methods=['POST'])
@login_required
@admin_required
def delete_trek(trek_id):
    trek = Trek.query.get_or_404(trek_id)
    db.session.delete(trek)
    db.session.commit()
    flash('Trek deleted.', 'info')
    return redirect(url_for('admin.manage_treks'))
@admin_bp.route('/staff')
@login_required
@admin_required
def manage_staff():
    pending_staff = User.query.filter_by(role='staff', status='pending').all()
    approved_staff = User.query.filter_by(role='staff', status='approved').all()
    blacklisted_staff = User.query.filter_by(role='staff', status='blacklisted').all()

    return render_template(
        'admin/staff.html',
        pending_staff=pending_staff,
        approved_staff=approved_staff,
        blacklisted_staff=blacklisted_staff,
        active_page='staff'
    )


@admin_bp.route('/staff/approve/<int:staff_id>', methods=['POST'])
@login_required
@admin_required
def approve_staff(staff_id):
    staff = User.query.get_or_404(staff_id)
    staff.status = 'approved'
    db.session.commit()
    flash(f'{staff.name} approved successfully.', 'success')
    return redirect(url_for('admin.manage_staff'))


@admin_bp.route('/staff/reject/<int:staff_id>', methods=['POST'])
@login_required
@admin_required
def reject_staff(staff_id):
    staff = User.query.get_or_404(staff_id)
    db.session.delete(staff)
    db.session.commit()
    flash('Staff request rejected.', 'info')
    return redirect(url_for('admin.manage_staff'))


@admin_bp.route('/staff/blacklist/<int:staff_id>', methods=['POST'])
@login_required
@admin_required
def blacklist_staff(staff_id):
    staff = User.query.get_or_404(staff_id)
    staff.status = 'blacklisted'
    db.session.commit()
    flash(f'{staff.name} has been blacklisted.', 'warning')
    return redirect(url_for('admin.manage_staff'))


@admin_bp.route('/staff/reinstate/<int:staff_id>', methods=['POST'])
@login_required
@admin_required
def reinstate_staff(staff_id):
    staff = User.query.get_or_404(staff_id)
    staff.status = 'approved'
    db.session.commit()
    flash(f'{staff.name} reinstated.', 'success')
    return redirect(url_for('admin.manage_staff'))
@admin_bp.route('/users')
@login_required
@admin_required
def manage_users():
    search = request.args.get('search', '')
    query = User.query.filter_by(role='user')
    if search:
        query = query.filter(User.name.ilike(f'%{search}%'))
    users = query.all()
    return render_template('admin/users.html', users=users, active_page='users')


@admin_bp.route('/users/blacklist/<int:user_id>', methods=['POST'])
@login_required
@admin_required
def blacklist_user(user_id):
    user = User.query.get_or_404(user_id)
    user.status = 'blacklisted'
    db.session.commit()
    flash(f'{user.name} has been blacklisted.', 'warning')
    return redirect(url_for('admin.manage_users'))


@admin_bp.route('/users/reinstate/<int:user_id>', methods=['POST'])
@login_required
@admin_required
def reinstate_user(user_id):
    user = User.query.get_or_404(user_id)
    user.status = 'active'
    db.session.commit()
    flash(f'{user.name} reinstated.', 'success')
    return redirect(url_for('admin.manage_users'))
@admin_bp.route('/bookings')
@login_required
@admin_required
def all_bookings():
    bookings = Booking.query.order_by(Booking.booking_date.desc()).all()
    return render_template('admin/bookings.html', bookings=bookings, active_page='bookings')
@admin_bp.route('/search')
@login_required
@admin_required
def search():
    query_str = request.args.get('q', '')
    treks, staff, users = [], [], []

    if query_str:
        treks = Trek.query.filter(
            (Trek.name.ilike(f'%{query_str}%')) | (Trek.id == query_str if query_str.isdigit() else False)
        ).all()
        staff = User.query.filter_by(role='staff').filter(
            (User.name.ilike(f'%{query_str}%')) | (User.id == query_str if query_str.isdigit() else False)
        ).all()
        users = User.query.filter_by(role='user').filter(
            (User.name.ilike(f'%{query_str}%')) | (User.id == query_str if query_str.isdigit() else False)
        ).all()

    return render_template('admin/search.html', query_str=query_str, treks=treks, staff=staff, users=users, active_page='search')