import os
import requests
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

# Import models cleanly from package
from models import db, User, Attendance, Timetable

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'kings-spark-secret-key-2026')

# Render PostgreSQL connection with local SQLite fallback
db_url = os.environ.get('DATABASE_URL', 'sqlite:///kings_spark.db')
if db_url and db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql://", 1)

app.config['SQLALCHEMY_DATABASE_URI'] = db_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = os.path.join('static', 'uploads')

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

db.init_app(app)

# Login Manager Setup
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    try:
        return User.query.get(int(user_id))
    except Exception:
        return None

# Auto-create tables & seed default admin user
with app.app_context():
    db.create_all()
    admin_user = User.query.filter_by(username='admin').first()
    if not admin_user:
        admin_user = User(username='admin', role='admin')
        if hasattr(admin_user, 'full_name'):
            admin_user.full_name = 'System Administrator'
        if hasattr(admin_user, 'email'):
            admin_user.email = 'admin@kingsspark.com'
        if hasattr(admin_user, 'set_password'):
            admin_user.set_password('admin123')
        else:
            admin_user.password_hash = generate_password_hash('admin123')
        db.session.add(admin_user)
        db.session.commit()
        print("Default admin created successfully!")

# --- Application Routes ---
@app.route('/')
def home():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()

        if user and user.check_password(password):
            login_user(user)
            flash('Logged in successfully!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password.', 'danger')

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
    return render_template('dashboard.html')

@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if request.method == 'POST':
        email = request.form.get('email')
        current_pass = request.form.get('current_password')
        new_pass = request.form.get('new_password')

        if hasattr(current_user, 'email'):
            current_user.email = email

        if current_pass and new_pass:
            if current_user.check_password(current_pass):
                current_user.set_password(new_pass)
                flash('Password updated successfully!', 'success')
            else:
                flash('Incorrect current password.', 'danger')

        db.session.commit()
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('profile'))

    return render_template('profile.html', user=current_user)

@app.route('/upload_passport', methods=['POST'])
@login_required
def upload_passport():
    if 'passport' not in request.files:
        flash('No file selected.', 'danger')
        return redirect(url_for('profile'))

    file = request.files['passport']
    if file and file.filename != '':
        filename = secure_filename(f"user_{current_user.id}_{file.filename}")
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)

        if hasattr(current_user, 'passport_photo'):
            current_user.passport_photo = f"uploads/{filename}"
            db.session.commit()
            flash('File uploaded successfully!', 'success')

    return redirect(url_for('profile'))

@app.route('/admin/attendance', methods=['GET', 'POST'])
@login_required
def manage_attendance():
    if current_user.role != 'admin':
        flash('Unauthorized access.', 'danger')
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        student_id = request.form.get('student_id')
        date = request.form.get('date')
        status = request.form.get('status')
        class_name = request.form.get('class_name')

        record = Attendance(student_id=student_id, date=date, status=status, class_name=class_name)
        db.session.add(record)
        db.session.commit()
        flash('Attendance record saved!', 'success')
        return redirect(url_for('manage_attendance'))

    students = User.query.filter_by(role='student').all()
    records = Attendance.query.order_by(Attendance.date.desc()).all()
    return render_template('manage_attendance.html', students=students, records=records)

@app.route('/admin/timetable', methods=['GET', 'POST'])
@login_required
def manage_timetable():
    if current_user.role != 'admin':
        flash('Unauthorized access.', 'danger')
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        class_name = request.form.get('class_name')
        day = request.form.get('day')
        time_slot = request.form.get('time_slot')
        subject = request.form.get('subject')
        teacher_name = request.form.get('teacher_name')

        entry = Timetable(class_name=class_name, day=day, time_slot=time_slot, subject=subject, teacher_name=teacher_name)
        db.session.add(entry)
        db.session.commit()
        flash('Timetable slot added!', 'success')
        return redirect(url_for('manage_timetable'))

    entries = Timetable.query.order_by(Timetable.class_name, Timetable.day).all()
    return render_template('manage_timetable.html', entries=entries)

@app.route('/view_schedule')
@login_required
def view_schedule():
    timetables = Timetable.query.order_by(Timetable.day, Timetable.time_slot).all()
    attendance = []
    if current_user.role == 'student':
        attendance = Attendance.query.filter_by(student_id=current_user.id).order_by(Attendance.date.desc()).all()
    return render_template('view_schedule.html', timetables=timetables, attendance=attendance)

if __name__ == '__main__':
    app.run(debug=True)
