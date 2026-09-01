from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

# Import models directly from submodules to avoid duplicate table declarations
from models.user import User, StudentProfile, TeacherProfile
from models.academic import AcademicSession, Subject, Score, FeeStructure, FeePayment, Timetable

# If Attendance is in models/academic.py or another submodule, import it here:
try:
    from models.academic import Attendance
except ImportError:
    class Attendance(db.Model):
        id = db.Column(db.Integer, primary_key=True)
        student_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
        date = db.Column(db.String(20), nullable=False)
        status = db.Column(db.String(10), nullable=False)
        class_name = db.Column(db.String(50), nullable=False)
        student = db.relationship('User', backref='attendance_records')
