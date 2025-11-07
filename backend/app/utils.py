import uuid

def generate_unique_id():
    return uuid.uuid4().hex
from flask import jsonify
import re
import bcrypt
import jwt
from datetime import datetime, timedelta
from functools import wraps
from flask import request


def success_response(data, status_code=200):
    """
    Return a standardized success response
    
    Args:
        data: The data to return
        status_code: HTTP status code (default: 200)
    
    Returns:
        Flask response object
    """
    response = {
        'success': True,
        'data': data
    }
    return jsonify(response), status_code


def error_response(message, status_code=400):
    """
    Return a standardized error response
    
    Args:
        message: Error message
        status_code: HTTP status code (default: 400)
    
    Returns:
        Flask response object
    """
    response = {
        'success': False,
        'error': message
    }
    return jsonify(response), status_code


def paginate_query(query, page=1, per_page=10):
    """
    Paginate a SQLAlchemy query
    
    Args:
        query: SQLAlchemy query object
        page: Page number (default: 1)
        per_page: Items per page (default: 10)
    
    Returns:
        Dictionary with pagination data
    """
    paginated = query.paginate(page=page, per_page=per_page, error_out=False)
    
    return {
        'items': [item.to_dict() for item in paginated.items],
        'total': paginated.total,
        'pages': paginated.pages,
        'current_page': page,
        'per_page': per_page,
        'has_next': paginated.has_next,
        'has_prev': paginated.has_prev
    }


def validate_email(email):
    if not email or not isinstance(email, str):
        return False
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email.strip()) is not None


def validate_username(username):
    if not username or not isinstance(username, str):
        return False
    username = username.strip()
    if len(username) < 3 or len(username) > 80:
        return False
    return re.match(r'^[a-zA-Z0-9_]+$', username) is not None


def validate_password(password):
    if not password or not isinstance(password, str):
        return False
    if len(password) < 8:
        return False
    has_upper = any(c.isupper() for c in password)
    has_lower = any(c.islower() for c in password)
    has_digit = any(c.isdigit() for c in password)
    return has_upper and has_lower and has_digit


def hash_password(password):
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')


def verify_password(password, password_hash):
    return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))


def generate_token(user_id, secret_key, expiration_hours=24):
    payload = {
        'user_id': user_id,
        'exp': datetime.utcnow() + timedelta(hours=expiration_hours),
        'iat': datetime.utcnow()
    }
    return jwt.encode(payload, secret_key, algorithm='HS256')


def decode_token(token, secret_key):
    try:
        payload = jwt.decode(token, secret_key, algorithms=['HS256'])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


def require_auth(secret_key):
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            auth_header = request.headers.get('Authorization')
            if not auth_header:
                return error_response('Az Authorization fejléc hiányzik', 401)
            
            parts = auth_header.split()
            if len(parts) != 2 or parts[0].lower() != 'bearer':
                return error_response('Érvénytelen Authorization fejléc formátum', 401)
            
            token = parts[1]
            payload = decode_token(token, secret_key)
            if not payload:
                return error_response('Érvénytelen vagy lejárt token', 401)
            
            request.user_id = payload['user_id']
            return f(*args, **kwargs)
        return wrapper
    return decorator
