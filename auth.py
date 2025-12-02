from flask import Blueprint, request, jsonify, g, current_app
from models import db, User
from functools import wraps
import jwt
from datetime import datetime, timedelta, timezone
from typing import Callable, Any, Tuple, Union
from flask import Blueprint, request, jsonify, g, redirect
import os
from flask_mail import Mail, Message
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature
from config import get_config

auth_bp = Blueprint('auth_bp', __name__)

config = get_config()
JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', getattr(config, 'SECRET_KEY', 'default-secret-key-change-this'))

s = URLSafeTimedSerializer(JWT_SECRET_KEY)

import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def token_required(f: Callable) -> Callable:
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Bypass authentication for OPTIONS method to allow CORS preflight
        if request.method == 'OPTIONS':
            return f(*args, **kwargs)
        logger.debug(f"JWT_SECRET_KEY used: {JWT_SECRET_KEY}")
        token = request.headers.get('Authorization')
        if not token:
            logger.debug("Token is missing in request headers")
            return jsonify({'error': 'Token is missing'}), 401
        try:
            if token.startswith('Bearer '):
                token = token[7:]
            data = jwt.decode(token, JWT_SECRET_KEY, algorithms=['HS256'])
            current_user = db.session.get(User, data['user_id'])
            if not current_user:
                logger.debug("Current user not found for token user_id")
                return jsonify({'error': 'User not found'}), 401
            if not current_user.is_confirmed:
                logger.debug("User email not confirmed")
                return jsonify({'error': 'Email not confirmed'}), 401
            g.current_user = current_user
        except jwt.ExpiredSignatureError:
            logger.debug("Token has expired")
            return jsonify({'error': 'Token has expired'}), 401
        except jwt.InvalidTokenError:
            logger.debug("Invalid token")
            return jsonify({'error': 'Invalid token'}), 401
        return f(*args, **kwargs)
    return decorated_function

@auth_bp.route('/users', methods=['GET'])
@token_required
def get_users():
    try:
        # Pagination parameters with defaults
        page = request.args.get('page', default=1, type=int)
        limit = request.args.get('limit', default=10, type=int)
        role_filter = request.args.get('role', default=None, type=str)
        email_filter = request.args.get('email', default=None, type=str)
        query = User.query

        if role_filter:
            query = query.filter(User.role == role_filter)
        if email_filter:
            query = query.filter(User.email.ilike(f"%{email_filter}%"))

        pagination = query.paginate(page=page, per_page=limit, error_out=False)
        users = pagination.items

        users_data = []
        for user in users:
            users_data.append({
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'role': user.role,
                'is_confirmed': user.is_confirmed
            })

        response = {
            'users': users_data,
            'total': pagination.total,
            'page': pagination.page,
            'pages': pagination.pages,
            'has_next': pagination.has_next,
            'has_prev': pagination.has_prev
        }

        return jsonify(response)
    except Exception as e:
        import logging
        logging.error(f"Error in get_users endpoint: {e}")
        return jsonify({'error': 'Internal server error'}), 500

# These will be set from current_app.config in the functions

def get_current_user():
    return g.current_user if hasattr(g, 'current_user') else None

def validate_required_fields(data, required_fields):
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    for field in required_fields:
        if field not in data:
            return jsonify({'error': f'Missing required field: {field}'}), 400
    return None

def db_operation_with_error_handling(operation_func: Callable[[], Any], success_message: Union[str, None] = None) -> Union[Tuple[Any, int], Any]:
    try:
        result = operation_func()
        db.session.commit()
        if success_message:
            return jsonify({'message': success_message}), 201
        return result
    except Exception:
        db.session.rollback()
        return jsonify({'error': 'Internal server error'}), 500

def send_confirmation_email(user: User, token: str):
    try:
        FRONTEND_BASE_URL = current_app.config.get('FRONTEND_BASE_URL', 'http://localhost:5000')
        EMAIL_SENDER = current_app.config.get('MAIL_DEFAULT_SENDER', current_app.config.get('MAIL_USERNAME'))
        confirm_url = f"{FRONTEND_BASE_URL}/confirm_email?token={token}"
        subject = "Please confirm your email"
        body = f"Hi {user.username},\n\nPlease confirm your email by clicking the link below:\n{confirm_url}\n\nIf you did not register, please ignore this email.\n"
        msg = Message(subject, sender=EMAIL_SENDER, recipients=[user.email])
        msg.body = body
        current_app.mail.send(msg)
        logger.debug(f"Sent confirmation email to {user.email}")
    except Exception as e:
        logger.error(f"Failed to send confirmation email to {user.email}: {e}")
        raise


@auth_bp.route('/login', methods=['POST'])
def login_auth():
    try:
        data = request.json
        validation_error = validate_required_fields(data, ['email', 'password'])
        if validation_error:
            return validation_error

        user = User.query.filter_by(email=data['email']).first()
        if not user:
            return jsonify({'error': 'Email does not exist'}), 401

        # Check email confirmed
        if not user.is_confirmed:
            return jsonify({'error': 'Email not confirmed. Please verify your email before logging in.'}), 401

        if not user.check_password(data['password']):
            return jsonify({'error': 'Incorrect password'}), 401

        token = jwt.encode({
            'user_id': user.id,
            'exp': datetime.now(timezone.utc) + timedelta(hours=24)
        }, JWT_SECRET_KEY, algorithm='HS256')

        redirect_url = None
        if user.role == 'admin':
            redirect_url = 'admin_control_panel.html'
        elif user.role == 'teacher':
            redirect_url = 'teacher_dashboard.html'
        elif user.role == 'student':
            redirect_url = 'student_dashboard.html'

        return jsonify({
            'message': 'Login successful',
            'token': token,
            'user': {
                'id': user.id,
                'username': user.username,
                'role': user.role,
                'grade': user.grade,
                'email': user.email
            },
            'redirect': redirect_url
        })
    except Exception as e:
        logger.error(f"Error in login_auth: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@auth_bp.route('/register', methods=['POST'])
def register_auth():
    try:
        data = request.json
        logger.debug(f"Register data: {data}")
        phase = data.get('phase', 1)

        if phase == 1:
            validation_error = validate_required_fields(data, ['username', 'email', 'password', 'confirm_password'])
            if validation_error:
                return validation_error
            if data['password'] != data['confirm_password']:
                return jsonify({'error': 'Passwords do not match'}), 400
            return jsonify({
                'message': 'Phase 1 completed successfully',
                'phase': 1,
                'user_data': {
                    'username': data['username'],
                    'email': data['email']
                }
            }), 200

        elif phase == 2:
            validation_error = validate_required_fields(data, ['username', 'email', 'password', 'role'])
            if validation_error:
                return validation_error

            existing_user = User.query.filter_by(email=data['email']).first()
            if existing_user:
                return jsonify({'error': 'User with this email already exists'}), 409

            role = data['role']

            if role not in ['teacher', 'student']:
                return jsonify({'error': 'Invalid role selected'}), 400

            is_testing = data.get('is_testing', False)

            if role == 'teacher':
                def register_teacher_operation():
                    new_user = User(
                        username=data['username'],
                        email=data['email'],
                        role='teacher',
                        is_confirmed=is_testing
                    )
                    new_user.set_password(data['password'])
                    db.session.add(new_user)
                    db.session.flush()  # flush to generate id before sending email
                    # generate confirmation token
                    token = s.dumps({'user_id': new_user.id}, salt='email-confirm').decode('utf-8')
                    db.session.commit()
                    if not is_testing:
                        # send confirmation email in non-testing env
                        send_confirmation_email(new_user, token)
                    return jsonify({
                        'message': 'Registration successful. Please check your email to confirm your account.' if not is_testing else 'Registration successful (testing mode).',
                        'user_id': new_user.id,
                        'role': 'teacher',
                        'redirect': 'user_login.html'
                    }), 201
                return db_operation_with_error_handling(register_teacher_operation)

            elif role == 'student':
                validation_error = validate_required_fields(data, ['grade'])
                if validation_error:
                    return validation_error
                grade = data['grade']
                try:
                    grade_num = int(grade.replace('Grade ', ''))
                except:
                    return jsonify({'error': 'Invalid grade format'}), 400

                subjects = None
                stream = None
                if grade_num in [10, 11]:
                    validation_error = validate_required_fields(data, ['basket_subject_1', 'basket_subject_2', 'basket_subject_3'])
                    if validation_error:
                        return validation_error
                    subjects = ','.join([data['basket_subject_1'], data['basket_subject_2'], data['basket_subject_3']])
                elif grade_num in [12, 13]:
                    validation_error = validate_required_fields(data, ['stream'])
                    if validation_error:
                        return validation_error
                    stream = data['stream']
                    valid_streams = ['Science Stream', 'Commerce Stream', 'Arts Stream', 'Technology Stream']
                    if stream not in valid_streams:
                        return jsonify({'error': 'Invalid stream selected'}), 400
                    subjects = stream
                else:
                    subjects = None

                def register_student_operation():
                    new_user = User(
                        username=data['username'],
                        email=data['email'],
                        role='student',
                        grade=grade,
                        subjects=subjects,
                        is_confirmed=is_testing
                    )
                    new_user.set_password(data['password'])
                    db.session.add(new_user)
                    db.session.flush()  # flush to generate id before sending email
                    # generate confirmation token
                    token = s.dumps({'user_id': new_user.id}, salt='email-confirm').decode('utf-8')
                    db.session.commit()
                    if not is_testing:
                        # send confirmation email in non-testing env
                        try:
                            send_confirmation_email(new_user, token)
                        except Exception as e:
                            logger.error(f"Failed to send confirmation email: {e}")
                            # Continue without failing the registration
                    return jsonify({
                        'message': 'Registration successful. Please check your email to confirm your account.' if not is_testing else 'Registration successful (testing mode).',
                        'user_id': new_user.id,
                        'role': 'student',
                        'grade': grade,
                        'subjects': subjects,
                        'redirect': 'user_login.html'
                    }), 201

                return db_operation_with_error_handling(register_student_operation)

            else:
                return jsonify({'error': 'Invalid registration phase'}), 400
    except Exception as e:
        logger.error(f"Error in register_auth: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@auth_bp.route('/confirm_email', methods=['GET'])
def confirm_email():
    token = request.args.get('token')
    if not token:
        return jsonify({'error': 'Missing token'}), 400
    try:
        data = s.loads(token, salt='email-confirm', max_age=86400)  # 24 hours
        user = User.query.get(data['user_id'])
        if not user:
            return jsonify({'error': 'Invalid token user'}), 400
        if user.is_confirmed:
            return jsonify({'message': 'Email already confirmed'}), 200
        user.is_confirmed = True
        db.session.commit()
        # Redirect to login page after confirmation
        return redirect('/pages/user_login.html')
    except SignatureExpired:
        return jsonify({'error': 'Confirmation token expired'}), 400
    except BadSignature:
        return jsonify({'error': 'Invalid confirmation token'}), 400

@auth_bp.route('/test_email_send', methods=['GET'])
def test_email_send():
    import traceback
    test_email = 'thuvask001@gmail.com'  # Set your actual test email here
    try:
        EMAIL_SENDER = current_app.config.get('MAIL_DEFAULT_SENDER', current_app.config.get('MAIL_USERNAME'))
        from secrets import token_hex
        token = token_hex(16)
        subject = "Test Email from Edu Tech LMS"
        body = f"This is a test email from Edu Tech LMS.\nToken: {token}"
        msg = Message(subject, sender=EMAIL_SENDER, recipients=[test_email])
        msg.body = body
        current_app.mail.send(msg)
        return jsonify({'message': f'Test email successfully sent to {test_email}'}), 200
    except Exception as e:
        tb_str = traceback.format_exc()
        return jsonify({'error': f'Failed to send test email: {str(e)}', 'traceback': tb_str}), 500

