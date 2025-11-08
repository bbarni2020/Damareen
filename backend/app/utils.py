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


def require_auth(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        from flask import current_app
        from app.models import User
        
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            return error_response('Az Authorization fejléc hiányzik', 401)
        
        parts = auth_header.split()
        if len(parts) != 2 or parts[0].lower() != 'bearer':
            return error_response('Érvénytelen Authorization fejléc formátum', 401)
        
        token = parts[1]
        payload = decode_token(token, current_app.config['SECRET_KEY'])
        if not payload:
            return error_response('Érvénytelen vagy lejárt token', 401)
        
        user_id = payload['user_id']
        user = User.query.get(user_id)
        
        if not user:
            return error_response('Felhasználó nem található', 401)
        
        request.user_id = user_id
        request.current_user = user
        return f(*args, **kwargs)
    return decorated_function


def is_master_of_world(user, world_id):
    if not user or not user.world_ids:
        return False
    return user.world_ids.get(str(world_id)) is True


def require_master(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user = request.current_user
        data = request.get_json(silent=True)
        
        world_id = data.get('world_id') if data else None
        if not world_id:
            world_id = request.args.get('world_id')
        
        if not world_id:
            return error_response('A világ azonosítója kötelező', 400)
        
        if not is_master_of_world(user, world_id):
            return error_response('Nincs jogosultságod ehhez a művelethez', 403)
        
        return f(*args, **kwargs)
    return decorated_function


def check_master_status():
    user = request.current_user
    world_id = request.args.get('world_id')
    
    if not world_id:
        return error_response('A világ azonosítója kötelező', 400)
    
    is_master = is_master_of_world(user, world_id)
    
    return success_response({
        'is_master': is_master,
        'world_id': world_id
    })
