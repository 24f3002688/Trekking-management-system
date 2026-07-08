from flask import Blueprint, render_template
from flask_login import login_required, current_user
from models import db, User, Trek, Booking

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
        recent_bookings=recent_bookings
    )