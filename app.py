from flask import Flask, render_template
from config import Config
from models import db, User
from werkzeug.security import generate_password_hash
from flask_login import LoginManager

login_manager = LoginManager()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    from routes.auth import auth_bp
    app.register_blueprint(auth_bp, url_prefix='/auth')
    from routes.admin import admin_bp
    app.register_blueprint(admin_bp, url_prefix='/admin')
    from routes.staff import staff_bp
    app.register_blueprint(staff_bp, url_prefix='/staff')

    with app.app_context():
        db.create_all()
        seed_admin()

    @app.route('/')
    def home():
        return render_template('home.html')

    return app


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


def seed_admin():
    existing_admin = User.query.filter_by(role='admin').first()
    if not existing_admin:
        admin = User(
            name='Admin',
            email='admin@trekking.com',
            password=generate_password_hash('admin123'),
            role='admin',
            status='active'
        )
        db.session.add(admin)
        db.session.commit()
        print("Admin account created: admin@trekking.com / admin123")
    else:
        print("Admin already exists, skipping seed.")


app = create_app()

if __name__ == '__main__':
    app.run(debug=True)