from flask import Flask, jsonify, send_from_directory
from flask_cors import CORS
from models import db
from dotenv import load_dotenv
from config import get_config
import os
from utils.logging_setup import setup_logging
from flask_talisman import Talisman
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_migrate import Migrate

load_dotenv()

app = Flask(__name__)
# Temporarily allow CORS from all origins with credentials to fix preflight errors
CORS(app, resources={r"/*": {"origins": "*"}}, supports_credentials=True)

# Enable security headers via Flask-Talisman
Talisman(app, content_security_policy=None)

# Setup rate limiter
redis_url = os.environ.get('REDIS_URL')
if redis_url:
    limiter = Limiter(
        key_func=get_remote_address,
        default_limits=["200 per day", "50 per hour"],
        storage_uri=redis_url
    )
else:
    limiter = Limiter(
        key_func=get_remote_address,
        default_limits=["200 per day", "50 per hour"],
        storage_uri="memory://"
    )
limiter.init_app(app)

# Initialize Flask-Mail
from flask_mail import Mail
mail = Mail(app)

config_class = get_config()
app.config.from_object(config_class)

# Initialize Flask-Mail after config
from flask_mail import Mail
mail = Mail(app)

# Setup logging
setup_logging(app)

# Global error handler for JSON responses
@app.errorhandler(Exception)
def handle_exception(e):
    from werkzeug.exceptions import HTTPException
    if isinstance(e, HTTPException):
        return jsonify({'error': e.description}), e.code
    return jsonify({'error': 'Internal Server Error'}), 500

UPLOAD_FOLDER = app.config.get('UPLOAD_FOLDER', 'uploads')

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

db.init_app(app)

# Initialize Flask-Migrate
migrate = Migrate(app, db)

# Register Blueprints
from auth import auth_bp
from lessons import lessons_bp
from quizzes import quizzes_bp
from teacher import teacher_bp
from student import students_bp
from progress import progress_bp

app.register_blueprint(auth_bp, url_prefix='/api')
app.register_blueprint(lessons_bp)
app.register_blueprint(quizzes_bp)
app.register_blueprint(teacher_bp)
app.register_blueprint(students_bp)
app.register_blueprint(progress_bp)

# Serve static files and pages
@app.route('/pages/<path:filename>')
def serve_pages(filename):
    return send_from_directory('pages', filename)

@app.route('/css/<path:filename>')
def serve_css(filename):
    return send_from_directory('css', filename)

@app.route('/public/<path:filename>')
def serve_public(filename):
    return send_from_directory('public', filename)

@app.route('/uploads/<path:filename>')
def serve_uploads(filename):
    return send_from_directory('uploads', filename)

@app.route('/')
def index():
    return send_from_directory('pages', 'landing_page.html')

@app.route('/user_registration.html')
def serve_user_registration():
    return send_from_directory('pages', 'user_registration.html')

@app.route('/user_login.html')
def serve_user_login():
    return send_from_directory('pages', 'user_login.html')

@app.route('/landing_page.html')
def serve_landing_page():
    return send_from_directory('pages', 'landing_page.html')

@app.route('/student_dashboard.html')
def serve_student_dashboard():
    return send_from_directory('pages', 'student_dashboard.html')

@app.route('/student_lessons.html')
def serve_student_lessons():
    return send_from_directory('pages', 'student_lessons.html')

@app.route('/student_quizzes.html')
def serve_student_quizzes():
    return send_from_directory('pages', 'student_quizzes.html')

@app.route('/student_ai_tutor.html')
def serve_student_ai_tutor():
    return send_from_directory('pages', 'student_ai_tutor.html')

@app.route('/student_profile.html')
def serve_student_profile():
    return send_from_directory('pages', 'student_profile.html')

@app.route('/teacher_dashboard.html')
def serve_teacher_dashboard():
    return send_from_directory('pages', 'teacher_dashboard.html')

@app.route('/admin_dashboard.html')
def serve_admin_dashboard():
    return send_from_directory('pages', 'admin_dashboard.html')

@app.route('/admin_control_panel.html')
def serve_admin_control_panel():
    return send_from_directory('pages', 'admin_control_panel.html')

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=app.config['DEBUG'])
