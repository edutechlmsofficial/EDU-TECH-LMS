from flask import Blueprint, jsonify, request
from models import db, Quiz
from auth import token_required, get_current_user
import json
from utils.validation import validate_required_fields, role_required

quizzes_bp = Blueprint('quizzes_bp', __name__, url_prefix='/api/quizzes')

@quizzes_bp.route('', methods=['GET'])
def get_quizzes():
    quizzes = Quiz.query.all()
    return jsonify([quiz.to_dict() for quiz in quizzes])

@quizzes_bp.route('/<int:quiz_id>', methods=['GET'])
def get_quiz(quiz_id):
    quiz = Quiz.query.get_or_404(quiz_id)
    return jsonify(quiz.to_dict())

@quizzes_bp.route('', methods=['POST'])
@token_required
@role_required('teacher')
@validate_required_fields(['title', 'subject', 'grade', 'questions'])
def create_quiz():
    user = get_current_user()
    data = request.get_json()
    questions_json = json.dumps(data.get('questions', []))
    quiz = Quiz(
        title=data.get('title'),
        subject=data.get('subject'),
        grade=data.get('grade'),
        questions=questions_json,
        teacher_id=user.id
    )
    db.session.add(quiz)
    db.session.commit()
    return jsonify(quiz.to_dict()), 201

@quizzes_bp.route('/<int:quiz_id>', methods=['PUT'])
@token_required
@role_required('teacher')
def update_quiz(quiz_id):
    user = get_current_user()
    quiz = Quiz.query.get_or_404(quiz_id)
    if quiz.teacher_id != user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    data = request.get_json()
    if 'questions' in data:
        quiz.questions = json.dumps(data['questions'])
    quiz.title = data.get('title', quiz.title)
    quiz.subject = data.get('subject', quiz.subject)
    quiz.grade = data.get('grade', quiz.grade)
    db.session.commit()
    return jsonify(quiz.to_dict())

@quizzes_bp.route('/<int:quiz_id>', methods=['DELETE'])
@token_required
@role_required('teacher')
def delete_quiz(quiz_id):
    user = get_current_user()
    quiz = Quiz.query.get_or_404(quiz_id)
    if quiz.teacher_id != user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    db.session.delete(quiz)
    db.session.commit()
    return jsonify({'message': 'Quiz deleted'})
