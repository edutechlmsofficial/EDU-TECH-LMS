from flask import Blueprint, jsonify, request
from flask_cors import CORS
from models import db, Lesson, Quiz, QuizResult
from auth import token_required, get_current_user
import json
from datetime import datetime, timezone
from utils.validation import role_required, validate_required_fields


students_bp = Blueprint('students_bp', __name__, url_prefix='/api/student')
CORS(students_bp)

@students_bp.route('/lessons', methods=['GET'])
@token_required
@role_required('student')
def get_student_lessons():
    lessons = Lesson.query.all()
    return jsonify([lesson.to_dict() for lesson in lessons])

@students_bp.route('/lessons', methods=['OPTIONS'])
def options_student_lessons():
    return '', 200

@students_bp.route('/quizzes', methods=['GET'])
@token_required
@role_required('student')
def get_student_quizzes():
    quizzes = Quiz.query.all()
    return jsonify([quiz.to_dict() for quiz in quizzes])

@students_bp.route('/quizzes', methods=['OPTIONS'])
def options_student_quizzes():
    return '', 200

@students_bp.route('/quizzes/attempts', methods=['GET'])
@token_required
@role_required('student')
def get_quiz_attempts():
    user = get_current_user()
    attempts = QuizResult.query.filter_by(student_id=user.id).all()
    return jsonify([attempt.to_dict() for attempt in attempts])

@students_bp.route('/dashboard', methods=['GET'])
@token_required
@role_required('student')
def get_student_dashboard():
    user = get_current_user()

    total_lessons = Lesson.query.count()
    total_quizzes = Quiz.query.count()
    quizzes_taken = QuizResult.query.filter_by(student_id=user.id).count()
    latest_result = QuizResult.query.filter_by(student_id=user.id).order_by(QuizResult.submitted_date.desc()).first()

    dashboard = {
        'total_lessons': total_lessons,
        'total_quizzes': total_quizzes,
        'quizzes_taken': quizzes_taken,
        'latest_quiz_result': latest_result.to_dict() if latest_result else None
    }
    return jsonify(dashboard)

@students_bp.route('/dashboard', methods=['OPTIONS'])
def options_student_dashboard():
    return '', 200

@students_bp.route('/quizzes/<int:quiz_id>/submit', methods=['POST'])
@token_required
@role_required('student')
@validate_required_fields(['answers'])
def submit_quiz(quiz_id):
    user = get_current_user()
    data = request.get_json()
    answers = data.get('answers')

    quiz = Quiz.query.get_or_404(quiz_id)

    quiz_result = QuizResult(
        quiz_id=quiz.id,
        student_id=user.id,
        answers=json.dumps(answers),
        submitted_date=datetime.now(timezone.utc)
    )
    db.session.add(quiz_result)
    db.session.commit()

    return jsonify({'message': 'Quiz submitted successfully'})
