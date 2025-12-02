from functools import wraps
from flask import request, jsonify, g
import jwt
from jwt import ExpiredSignatureError

def validate_required_fields(required_fields):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            data = request.get_json(silent=True)
            if not data:
                return jsonify({'error': 'No data provided'}), 400
            missing_fields = [field for field in required_fields if not data.get(field)]
            if missing_fields:
                return jsonify({'error': 'Missing required fields', 'fields': missing_fields}), 400
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def role_required(*allowed_roles):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            user = getattr(g, 'current_user', None)
            if not user or user.role not in allowed_roles:
                return jsonify({'error': 'Unauthorized'}), 403
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def authorize_teacher(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user = getattr(g, 'current_user', None)
        if not user or user.role != 'teacher':
            return jsonify({'error': 'Unauthorized'}), 403
        return f(*args, **kwargs)
    return decorated_function

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        # JWT token expected in the Authorization header
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            parts = auth_header.split()
            if len(parts) == 2 and parts[0].lower() == 'bearer':
                token = parts[1]
        if not token:
            return jsonify({'message': 'Token is missing!'}), 401
        try:
            # Replace 'your_secret_key' with your actual secret key used for encoding the JWT
            data = jwt.decode(token, 'your_secret_key', algorithms=['HS256'])
            g.current_user = data  # store user info in flask.g for access in routes
        except ExpiredSignatureError:
            return jsonify({'message': 'Token has expired!'}), 401
        except jwt.DecodeError:
            return jsonify({'message': 'Token is invalid!'}), 401
        except Exception as e:
            return jsonify({'message': f'Could not verify token: {str(e)}'}), 401

        return f(*args, **kwargs)
    return decorated
