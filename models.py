
class Attendance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    date = db.Column(db.String(20), nullable=False)
    status = db.Column(db.String(10), nullable=False) # 'Present', 'Absent', 'Late'
    class_name = db.Column(db.String(50), nullable=False)
    student = db.relationship('User', backref='attendance_records')

class Timetable(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    class_name = db.Column(db.String(50), nullable=False)
    day = db.Column(db.String(20), nullable=False) # 'Monday', 'Tuesday', etc.
    time_slot = db.Column(db.String(30), nullable=False) # '08:00 AM - 09:00 AM'
    subject = db.Column(db.String(100), nullable=False)
    teacher_name = db.Column(db.String(100), nullable=False)
