from models import db
from flask_login import UserMixin
from datetime import datetime

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # 'admin', 'teacher', 'student'
    full_name = db.Column(db.String(120), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class StudentProfile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    admission_number = db.Column(db.String(50), unique=True, nullable=False)
    class_name = db.Column(db.String(20), nullable=False)
    parent_phone = db.Column(db.String(20), nullable=False)
    passport_image = db.Column(db.String(255), default='default.jpg')
    
    user = db.relationship('User', backref=db.backref('student_profile', uselist=False))

class TeacherProfile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    assigned_class = db.Column(db.String(20), nullable=False)
    
    user = db.relationship('User', backref=db.backref('teacher_profile', uselist=False))