from flask import Blueprint, request, jsonify
from flask_cors import CORS
from models import db, Progress
from auth import token_required, get_current_user
from datetime import datetime
from utils.validation import role_required, validate_required_fields

progress_bp = Blueprint('progress_bp', __name__, url_prefix='/api/progress')
CORS(progress_bp)

@progress_bp.route('', methods=['GET'])
@token_required
@role_required('student', 'teacher')
def get_progress():
    user = get_current_user()
    user_id = request.args.get('user_id')
    if not user_id:
        return jsonify({'error': 'Missing user_id parameter'}), 400
    if str(user.id) != user_id:
        return jsonify({'error': 'Unauthorized access'}), 403
    progress_records = Progress.query.filter_by(user_id=user.id).all()
    return jsonify([record.to_dict() for record in progress_records])

@progress_bp.route('', methods=['POST'])
@token_required
@validate_required_fields(['lesson_id'])
@role_required('student', 'teacher')
def update_progress():
    user = get_current_user()
    data = request.get_json()
    lesson_id = data.get('lesson_id')

    progress = Progress.query.filter_by(user_id=user.id, lesson_id=lesson_id).first()
    if not progress:
        progress = Progress(user_id=user.id, lesson_id=lesson_id, progress=0, last_updated=datetime.utcnow())
        db.session.add(progress)

    progress.progress = data.get('progress', progress.progress)
    progress.last_updated = datetime.utcnow()

    try:
        db.session.commit()
        return jsonify({'message': 'Progress updated successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to update progress'}), 500
