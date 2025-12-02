from flask import Blueprint, jsonify, request
from models import db, Lesson
from auth import token_required, get_current_user
from utils.validation import validate_required_fields, role_required

lessons_bp = Blueprint('lessons_bp', __name__, url_prefix='/api/lessons')

@lessons_bp.route('', methods=['GET'])
def get_lessons():
    lessons = Lesson.query.all()
    return jsonify([lesson.to_dict() for lesson in lessons])

@lessons_bp.route('/<int:lesson_id>', methods=['GET'])
def get_lesson(lesson_id):
    lesson = Lesson.query.get_or_404(lesson_id)
    return jsonify(lesson.to_dict())

@lessons_bp.route('', methods=['POST'])
@token_required
@role_required('teacher')
@validate_required_fields(['title', 'subject', 'grade', 'content'])
def create_lesson():
    user = get_current_user()
    data = request.get_json()
    lesson = Lesson(
        title=data.get('title'),
        subject=data.get('subject'),
        grade=data.get('grade'),
        content=data.get('content'),
        teacher_id=user.id
    )
    db.session.add(lesson)
    db.session.commit()
    return jsonify(lesson.to_dict()), 201

@lessons_bp.route('/<int:lesson_id>', methods=['PUT'])
@token_required
@role_required('teacher')
def update_lesson(lesson_id):
    user = get_current_user()
    lesson = Lesson.query.get_or_404(lesson_id)
    if lesson.teacher_id != user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    data = request.get_json()
    lesson.title = data.get('title', lesson.title)
    lesson.subject = data.get('subject', lesson.subject)
    lesson.grade = data.get('grade', lesson.grade)
    lesson.content = data.get('content', lesson.content)
    db.session.commit()
    return jsonify(lesson.to_dict())

@lessons_bp.route('/<int:lesson_id>', methods=['DELETE'])
@token_required
@role_required('teacher')
def delete_lesson(lesson_id):
    user = get_current_user()
    lesson = Lesson.query.get_or_404(lesson_id)
    if lesson.teacher_id != user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    db.session.delete(lesson)
    db.session.commit()
    return jsonify({'message': 'Lesson deleted'})
