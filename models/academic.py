from models import db
from datetime import datetime

class AcademicSession(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    session_name = db.Column(db.String(20), nullable=False)  # e.g., "2025/2026"
    term_name = db.Column(db.String(20), nullable=False)     # e.g., "First Term"
    is_active = db.Column(db.Boolean, default=True)
    is_results_published = db.Column(db.Boolean, default=False)

class Subject(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    code = db.Column(db.String(20), unique=True, nullable=False)

class FeeStructure(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    class_name = db.Column(db.String(20), nullable=False)
    session_id = db.Column(db.Integer, db.ForeignKey('academic_session.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)

class Timetable(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    class_name = db.Column(db.String(20), nullable=False)
    day = db.Column(db.String(15), nullable=False)
    time_slot = db.Column(db.String(50), nullable=False)
    subject_name = db.Column(db.String(100), nullable=False)

class Score(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    subject_id = db.Column(db.Integer, db.ForeignKey('subject.id'), nullable=False)
    session_id = db.Column(db.Integer, db.ForeignKey('academic_session.id'), nullable=False)
    ca1 = db.Column(db.Float, default=0.0)
    ca2 = db.Column(db.Float, default=0.0)
    exam = db.Column(db.Float, default=0.0)
    
    subject = db.relationship('Subject', backref='scores')
    student = db.relationship('User', backref='scores')

    @property
    def total_score(self):
        return self.ca1 + self.ca2 + self.exam

    @property
    def grade_and_remark(self):
        total = self.total_score
        if total >= 70: return 'A', 'Excellent'
        elif total >= 60: return 'B', 'Very Good'
        elif total >= 50: return 'C', 'Good'
        elif total >= 45: return 'D', 'Pass'
        elif total >= 40: return 'E', 'Fair'
        else: return 'F', 'Fail'

class FeePayment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    reference = db.Column(db.String(100), unique=True, nullable=False)
    amount = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), default='Pending')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)