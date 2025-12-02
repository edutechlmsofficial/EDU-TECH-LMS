from flask import Blueprint, jsonify
from models import db, User, Lesson, Quiz, QuizAttempt, LessonProgress
from auth import token_required, get_current_user
from utils.validation import role_required

teacher_bp = Blueprint('teacher_bp', __name__, url_prefix='/api/teacher')

@teacher_bp.route('/dashboard', methods=['GET'])
@token_required
@role_required('teacher')
def get_dashboard():
    try:
        user = get_current_user()

        teacher_id = user.id

        teacher_lessons = Lesson.query.filter_by(teacher_id=teacher_id).all()
        grades = list(set([lesson.grade for lesson in teacher_lessons]))
        total_students = User.query.filter(User.role == 'student', User.grade.in_(grades)).count()

        active_lessons = Lesson.query.filter_by(teacher_id=teacher_id, status='approved').count()

        pending_grades = QuizAttempt.query.join(Quiz).filter(Quiz.teacher_id == teacher_id, QuizAttempt.completed == True).count()

        avg_performance = db.session.query(db.func.avg(QuizAttempt.score)).join(Quiz).filter(Quiz.teacher_id == teacher_id).scalar()
        avg_performance = round(avg_performance * 100, 1) if avg_performance else 0

        dashboard_data = {
            'total_students': total_students,
            'active_lessons': active_lessons,
            'pending_grades': pending_grades,
            'avg_performance': avg_performance,
            'name': user.username if user else None
        }
        return jsonify(dashboard_data)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': 'Internal Server Error', 'details': str(e)}), 500

@teacher_bp.route('/classes', methods=['GET'])
@token_required
@role_required('teacher')
def get_classes():
    try:
        user = get_current_user()

        teacher_id = user.id
        lessons = Lesson.query.filter_by(teacher_id=teacher_id, status='approved').all()

        classes = {}
        for lesson in lessons:
            key = f"{lesson.grade} - {lesson.subject}"
            if key not in classes:
                classes[key] = {
                    'grade': lesson.grade,
                    'subject': lesson.subject,
                    'lesson_count': 0,
                    'student_count': User.query.filter_by(role='student', grade=lesson.grade).count()
                }
            classes[key]['lesson_count'] += 1

        return jsonify(list(classes.values()))
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': 'Internal Server Error', 'details': str(e)}), 500

@teacher_bp.route('/progress', methods=['GET'])
@token_required
@role_required('teacher')
def get_progress():
    try:
        user = get_current_user()

        teacher_id = user.id
        lessons = Lesson.query.filter_by(teacher_id=teacher_id).all()
        lesson_ids = [l.id for l in lessons]

        progress_records = LessonProgress.query.filter(LessonProgress.lesson_id.in_(lesson_ids)).all()

        total_progress = len(progress_records)
        completed = sum(1 for p in progress_records if p.completed)
        avg_progress = sum(p.progress_percentage for p in progress_records) / total_progress if total_progress > 0 else 0

        quiz_attempts = QuizAttempt.query.join(Quiz).filter(Quiz.teacher_id == teacher_id).all()
        avg_score = sum(a.score for a in quiz_attempts) / len(quiz_attempts) if quiz_attempts else 0

        return jsonify({
            'total_students': len(set(p.user_id for p in progress_records)),
            'avg_progress': round(avg_progress, 1),
            'completion_rate': round(completed / total_progress * 100, 1) if total_progress > 0 else 0,
            'avg_score': round(avg_score * 100, 1)
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': 'Internal Server Error', 'details': str(e)}), 500

@teacher_bp.route('/grading', methods=['GET'])
@token_required
@role_required('teacher')
def get_grading():
    try:
        user = get_current_user()

        teacher_id = user.id
        quizzes = Quiz.query.filter_by(teacher_id=teacher_id).all()

        grading_queue = []
        for quiz in quizzes:
            attempts = QuizAttempt.query.filter_by(quiz_id=quiz.id, completed=True).all()
            if attempts:
                grading_queue.append({
                    'quiz_id': quiz.id,
                    'title': quiz.title,
                    'grade': quiz.grade,
                    'subject': quiz.subject,
                    'pending_count': len(attempts),
                    'total_questions': len(quiz.questions) if quiz.questions else 0
                })

        return jsonify(grading_queue)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': 'Internal Server Error', 'details': str(e)}), 500

@teacher_bp.route('/lessons', methods=['GET'])
@token_required
@role_required('teacher')
def get_teacher_lessons():
    try:
        user = get_current_user()

        teacher_id = user.id
        lessons = Lesson.query.filter_by(teacher_id=teacher_id).all()
        lesson_list = []
        for lesson in lessons:
            lesson_list.append({
                'id': lesson.id,
                'title': lesson.title,
                'grade': lesson.grade,
                'subject': lesson.subject,
                'status': lesson.status
            })
        return jsonify(lesson_list)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': 'Internal Server Error', 'details': str(e)}), 500
