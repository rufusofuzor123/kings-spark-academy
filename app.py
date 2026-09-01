import os
import logging
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash

logging.basicConfig(level=logging.INFO)

from models import db, User, Attendance, Timetable

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'kings-spark-secret-key-2026')

db_url = os.environ.get('DATABASE_URL', 'sqlite:///kings_spark.db')
if db_url and db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql://", 1)

app.config['SQLALCHEMY_DATABASE_URI'] = db_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    "pool_pre_ping": True,
    "pool_recycle": 280,
}

db.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    try:
        return User.query.get(int(user_id))
    except Exception:
        db.session.rollback()
        return None

# Auto-Initialize Database & Admin User on Server Startup
with app.app_context():
    try:
        db.create_all()
        admin = User.query.filter_by(username='admin').first()
        if not admin:
            admin = User(username='admin', role='admin')
            if hasattr(admin, 'full_name'):
                admin.full_name = 'System Administrator'
            if hasattr(admin, 'set_password'):
                admin.set_password('admin123')
            else:
                admin.password_hash = generate_password_hash('admin123')
            db.session.add(admin)
            db.session.commit()
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Startup DB Error: {e}")

@app.route('/')
def home():
    try:
        return render_template('index.html')
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Home route error: {e}")
        return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        try:
            user = User.query.filter_by(username=username).first()
            if user:
                is_valid = False
                if hasattr(user, 'check_password'):
                    is_valid = user.check_password(password)
                elif hasattr(user, 'password_hash'):
                    is_valid = check_password_hash(user.password_hash, password)

                if is_valid:
                    login_user(user, remember=True)
                    return redirect(url_for('dashboard'))

            flash('Invalid username or password.', 'danger')
        except Exception as e:
            db.session.rollback()
            app.logger.error(f"Login processing error: {e}")
            flash('Error logging in.', 'danger')

    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logged out successfully.', 'info')
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html', user=current_user)

@app.route('/force-reset-db')
def force_reset_db():
    try:
        db.drop_all()
        db.create_all()
        admin = User(username='admin', role='admin')
        if hasattr(admin, 'full_name'):
            admin.full_name = 'System Administrator'
        if hasattr(admin, 'set_password'):
            admin.set_password('admin123')
        else:
            admin.password_hash = generate_password_hash('admin123')

        db.session.add(admin)
        db.session.commit()
        return "<h3>Database reset successfully! <a href='/login'>Login Here</a>.</h3>"
    except Exception as e:
        db.session.rollback()
        return f"Error resetting database: {str(e)}"

if __name__ == '__main__':
    app.run(debug=True)
