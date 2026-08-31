import os
import requests
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

from config import Config
from models import db
from models.user import User, StudentProfile, TeacherProfile
from models.academic import AcademicSession, Subject, Score, FeeStructure, FeePayment, Timetable

app = Flask(__name__)
app.config.from_object(Config)

db.init_app(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# SMS Integration Core Utility
def send_sms_to_parent(phone_number, message):
    payload = {
        "to": phone_number,
        "from": app.config['SMS_SENDER_ID'],
        "sms": message,
        "api_key": app.config['SMS_API_KEY']
    }
    try:
        requests.post("https://api.termii.com/api/sms/send", json=payload, timeout=5)
    except Exception as e:
        print(f"SMS Dispatch Failed: {e}")

# Database Initialization Command Hook
@app.before_request
def setup_database():
    app.before_request_funcs[None].remove(setup_database)
    db.create_all()
    # Seed Admin User if system is freshly initialized
    if not User.query.filter_by(role='admin').first():
        admin = User(
            username='admin',
            password_hash=generate_password_hash('admin123'),
            role='admin',
            full_name='System Administrator'
        )
        db.session.add(admin)
        db.session.commit()

# --- AUTHENTICATION ROUTES ---
@app.route('/', methods=['GET', 'POST'])
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            return redirect(url_for(f"{user.role}_dashboard"))
        flash('Invalid Username or Password', 'danger')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

# --- ADMIN ROUTES ---
@app.route('/admin/dashboard')
@login_required
def admin_dashboard():
    if current_user.role != 'admin': return redirect(url_for('login'))
    active_session = AcademicSession.query.filter_by(is_active=True).first()
    students = StudentProfile.query.all()
    teachers = TeacherProfile.query.all()
    subjects = Subject.query.all()
    fees = FeeStructure.query.all()
    return render_template('admin/dashboard.html', session=active_session, students=students, teachers=teachers, subjects=subjects, fees=fees)

@app.route('/admin/create-term', methods=['POST'])
@login_required
def create_term():
    if current_user.role != 'admin': return redirect(url_for('login'))
    session_name = request.form.get('session_name')
    term_name = request.form.get('term_name')
    
    AcademicSession.query.update({AcademicSession.is_active: False})
    new_session = AcademicSession(session_name=session_name, term_name=term_name, is_active=True)
    db.session.add(new_session)
    db.session.commit()
    
    flash(f'Term "{term_name}" for Session "{session_name}" activated.', 'success')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/register-student', methods=['POST'])
@login_required
def register_student():
    if current_user.role != 'admin': return redirect(url_for('login'))
    
    username = request.form['username']
    password = request.form['password']
    full_name = request.form['full_name']
    admission_number = request.form['admission_number']
    class_name = request.form['class_name']
    parent_phone = request.form['parent_phone']
    
    file = request.files.get('passport')
    filename = 'default.jpg'
    if file and file.filename != '':
        filename = secure_filename(f"{admission_number}_{file.filename}")
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

    user = User(username=username, password_hash=generate_password_hash(password), role='student', full_name=full_name)
    db.session.add(user)
    db.session.flush()

    student_profile = StudentProfile(
        user_id=user.id,
        admission_number=admission_number,
        class_name=class_name,
        parent_phone=parent_phone,
        passport_image=filename
    )
    db.session.add(student_profile)
    db.session.commit()
    
    flash(f'Student {full_name} registered successfully.', 'success')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/register-teacher', methods=['POST'])
@login_required
def register_teacher():
    if current_user.role != 'admin': return redirect(url_for('login'))
    
    user = User(
        username=request.form['username'],
        password_hash=generate_password_hash(request.form['password']),
        role='teacher',
        full_name=request.form['full_name']
    )
    db.session.add(user)
    db.session.flush()

    teacher = TeacherProfile(user_id=user.id, assigned_class=request.form['assigned_class'])
    db.session.add(teacher)
    db.session.commit()
    
    flash('Teacher registered successfully.', 'success')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/create-subject', methods=['POST'])
@login_required
def create_subject():
    if current_user.role != 'admin': return redirect(url_for('login'))
    subject = Subject(name=request.form['name'], code=request.form['code'])
    db.session.add(subject)
    db.session.commit()
    flash('Subject added to curriculum.', 'success')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/set-fee', methods=['POST'])
@login_required
def set_fee():
    if current_user.role != 'admin': return redirect(url_for('login'))
    active_session = AcademicSession.query.filter_by(is_active=True).first()
    if not active_session:
        flash('Create an active academic session first.', 'danger')
        return redirect(url_for('admin_dashboard'))
        
    fee = FeeStructure(
        class_name=request.form['class_name'],
        session_id=active_session.id,
        amount=float(request.form['amount'])
    )
    db.session.add(fee)
    db.session.commit()
    flash('Fee structure updated.', 'success')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/publish-results', methods=['POST'])
@login_required
def publish_results():
    if current_user.role != 'admin': return redirect(url_for('login'))
    
    session = AcademicSession.query.filter_by(is_active=True).first()
    if session:
        session.is_results_published = True
        db.session.commit()
        
        students = StudentProfile.query.all()
        for student in students:
            msg = f"Dear Parent, Results for {student.user.full_name} ({session.term_name}, {session.session_name}) have been published on the Kings Spark Academy Portal."
            send_sms_to_parent(student.parent_phone, msg)
            
        flash('Results published and SMS alerts dispatched to all parent contact numbers.', 'success')
    return redirect(url_for('admin_dashboard'))

# --- TEACHER ROUTES ---
@app.route('/teacher/dashboard')
@login_required
def teacher_dashboard():
    if current_user.role != 'teacher': return redirect(url_for('login'))
    teacher = TeacherProfile.query.filter_by(user_id=current_user.id).first()
    students = StudentProfile.query.filter_by(class_name=teacher.assigned_class).all()
    subjects = Subject.query.all()
    active_session = AcademicSession.query.filter_by(is_active=True).first()
    return render_template('teacher/dashboard.html', teacher=teacher, students=students, subjects=subjects, session=active_session)

@app.route('/teacher/enter-scores', methods=['GET', 'POST'])
@login_required
def enter_scores():
    if current_user.role != 'teacher': return redirect(url_for('login'))
    if request.method == 'POST':
        active_session = AcademicSession.query.filter_by(is_active=True).first()
        score = Score.query.filter_by(
            student_id=request.form['student_id'],
            subject_id=request.form['subject_id'],
            session_id=active_session.id
        ).first()

        if not score:
            score = Score(
                student_id=request.form['student_id'],
                subject_id=request.form['subject_id'],
                session_id=active_session.id
            )

        score.ca1 = float(request.form['ca1'])
        score.ca2 = float(request.form['ca2'])
        score.exam = float(request.form['exam'])
        
        db.session.add(score)
        db.session.commit()
        flash('Student scores compiled successfully.', 'success')
        return redirect(url_for('teacher_dashboard'))
    return render_template('teacher/enter_scores.html')

# --- STUDENT ROUTES ---
@app.route('/student/dashboard')
@login_required
def student_dashboard():
    if current_user.role != 'student': return redirect(url_for('login'))
    profile = StudentProfile.query.filter_by(user_id=current_user.id).first()
    active_session = AcademicSession.query.filter_by(is_active=True).first()
    
    fee = None
    if active_session:
        fee = FeeStructure.query.filter_by(class_name=profile.class_name, session_id=active_session.id).first()
        
    timetables = Timetable.query.filter_by(class_name=profile.class_name).all()
    return render_template('student/dashboard.html', profile=profile, session=active_session, fee=fee, timetables=timetables)

@app.route('/student/result-sheet')
@login_required
def result_sheet():
    if current_user.role != 'student': return redirect(url_for('login'))
    active_session = AcademicSession.query.filter_by(is_active=True).first()
    
    if not active_session or not active_session.is_results_published:
        flash('Results for the current academic session have not been released by the portal administrator.', 'warning')
        return redirect(url_for('student_dashboard'))
        
    profile = StudentProfile.query.filter_by(user_id=current_user.id).first()
    scores = Score.query.filter_by(student_id=current_user.id, session_id=active_session.id).all()
    return render_template('student/result_sheet.html', scores=scores, profile=profile, session=active_session)

@app.route('/student/initialize-payment', methods=['POST'])
@login_required
def initialize_payment():
    if current_user.role != 'student': return redirect(url_for('login'))
    
    amount = float(request.form.get('amount'))
    email = f"{current_user.username}@kingsspark.edu.ng"
    
    headers = {
        "Authorization": f"Bearer {app.config['PAYSTACK_SECRET_KEY']}",
        "Content-Type": "application/json"
    }
    
    data = {
        "email": email,
        "amount": int(amount * 100),  # Convert NGN to Kobo
        "callback_url": url_for('paystack_callback', _external=True)
    }
    
    res = requests.post("https://api.paystack.co/transaction/initialize", json=data, headers=headers)
    res_data = res.json()
    
    if res_data.get('status'):
        payment = FeePayment(
            student_id=current_user.id,
            reference=res_data['data']['reference'],
            amount=amount
        )
        db.session.add(payment)
        db.session.commit()
        return redirect(res_data['data']['authorization_url'])
    
    flash('Payment gateway connection failed. Please try again.', 'danger')
    return redirect(url_for('student_dashboard'))

@app.route('/student/paystack-callback')
@login_required
def paystack_callback():
    reference = request.args.get('reference')
    headers = {"Authorization": f"Bearer {app.config['PAYSTACK_SECRET_KEY']}"}
    
    res = requests.get(f"https://api.paystack.co/transaction/verify/{reference}", headers=headers)
    res_data = res.json()
    
    if res_data.get('status') and res_data['data']['status'] == 'success':
        payment = FeePayment.query.filter_by(reference=reference).first()
        if payment:
            payment.status = 'Successful'
            db.session.commit()
        flash('School Fee Payment Verified Successfully!', 'success')
    else:
        flash('Payment Verification Failed.', 'danger')
        
    return redirect(url_for('student_dashboard'))

if __name__ == '__main__':
    app.run(debug=True)