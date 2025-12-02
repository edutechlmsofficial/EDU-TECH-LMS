from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timezone

db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), default='student')  # student, teacher, admin
    status = db.Column(db.String(20), default='active')  # active, inactive, suspended
    is_confirmed = db.Column(db.Boolean, default=False)  # New field for email confirmation
    registered_date = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    last_activity = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    grade = db.Column(db.String(20))  # For students
    subjects = db.Column(db.Text)  # JSON string of subjects for students/teachers

    def set_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password, password)

class Lesson(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    subject = db.Column(db.String(50), nullable=False)
    grade = db.Column(db.String(20), nullable=False)
    content = db.Column(db.Text, nullable=False)
    teacher_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    status = db.Column(db.String(20), default='pending')  # pending, approved, rejected
    created_date = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    uploaded_date = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    # New fields for file attachments and media
    pdf_file = db.Column(db.String(500))  # Path to uploaded PDF file
    video_file = db.Column(db.String(500))  # Path to uploaded video file
    youtube_link = db.Column(db.String(500))  # YouTube video URL
    attachment_type = db.Column(db.String(20))  # 'pdf', 'video', 'youtube', 'text'

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'subject': self.subject,
            'grade': self.grade,
            'content': self.content,
            'teacher_id': self.teacher_id,
            'status': self.status,
            'created_date': self.created_date.isoformat() if self.created_date else None,
            'uploaded_date': self.uploaded_date.isoformat() if self.uploaded_date else None,
            'pdf_file': self.pdf_file,
            'video_file': self.video_file,
            'youtube_link': self.youtube_link,
            'attachment_type': self.attachment_type
        }

import json

class Quiz(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    subject = db.Column(db.String(50), nullable=False)
    grade = db.Column(db.String(20), nullable=False)
    questions = db.Column(db.Text, nullable=False)  # JSON string of questions
    teacher_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    status = db.Column(db.String(20), default='pending')  # pending, approved, rejected
    created_date = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    uploaded_date = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    # New fields for quiz attachments
    instructions = db.Column(db.Text)  # Additional instructions for the quiz
    time_limit = db.Column(db.Integer)  # Time limit in minutes (optional)

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'subject': self.subject,
            'grade': self.grade,
            'questions': json.loads(self.questions) if self.questions else [],
            'teacher_id': self.teacher_id,
            'status': self.status,
            'created_date': self.created_date.isoformat() if self.created_date else None,
            'uploaded_date': self.uploaded_date.isoformat() if self.uploaded_date else None,
            'instructions': self.instructions,
            'time_limit': self.time_limit
        }

class QuizAttempt(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    quiz_id = db.Column(db.Integer, db.ForeignKey('quiz.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    score = db.Column(db.Float, nullable=False)
    total_questions = db.Column(db.Integer, nullable=False)
    completed_date = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    time_taken = db.Column(db.Integer, default=0)  # Time taken in minutes
    attempted_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    completed = db.Column(db.Boolean, default=False)

class LessonProgress(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    lesson_id = db.Column(db.Integer, db.ForeignKey('lesson.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    progress_percentage = db.Column(db.Float, default=0.0)  # 0.0 to 100.0
    completed = db.Column(db.Boolean, default=False)
    last_accessed = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    time_spent = db.Column(db.Integer, default=0)  # Time spent in minutes

class QuizResult(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    quiz_id = db.Column(db.Integer, db.ForeignKey('quiz.id'), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    answers = db.Column(db.Text, nullable=False)  # Stored as JSON string
    submitted_date = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def to_dict(self):
        import json
        return {
            'id': self.id,
            'quiz_id': self.quiz_id,
            'student_id': self.student_id,
            'answers': json.loads(self.answers) if self.answers else [],
            'submitted_date': self.submitted_date.isoformat() if self.submitted_date else None
        }

class Progress(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    lesson_id = db.Column(db.Integer, db.ForeignKey('lesson.id'), nullable=False)
    progress = db.Column(db.Float, default=0.0)
    last_updated = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'lesson_id': self.lesson_id,
            'progress': self.progress,
            'last_updated': self.last_updated.isoformat() if self.last_updated else None
        }
