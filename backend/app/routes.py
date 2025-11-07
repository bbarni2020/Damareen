from flask import Blueprint, jsonify, request
import time
from functools import wraps
from datetime import datetime
from app.models import db, User, World, Card, Dungeon
from app.utils import (
    success_response, error_response, validate_email, 
    validate_username, validate_password, hash_password,
    verify_password, generate_token, require_auth, generate_unique_id
)
from app.email_service import (
    send_verification_email, send_login_verification_email,
    generate_verification_token, get_verification_expiry
)
from app.email_config import EmailConfig
from sqlalchemy.exc import IntegrityError


api = Blueprint('api', __name__)

_rate_limit_store = {}
_RATE_LIMIT_WINDOW = 10 
_RATE_LIMIT_MAX = 5

def ratelimit(func):
    @wraps(func)
    def decorated_function(*args, **kwargs):
        ip = request.remote_addr or 'unknown'
        key = f"{ip}:{request.endpoint}"
        now = time.time()
        window_start = now - _RATE_LIMIT_WINDOW
        reqs = _rate_limit_store.get(key, [])
        reqs = [t for t in reqs if t > window_start]
        if len(reqs) >= _RATE_LIMIT_MAX:
            return error_response('Kéréskorlát túllépve', 429)
        reqs.append(now)
        _rate_limit_store[key] = reqs
        return func(*args, **kwargs)
    return decorated_function


@api.route('/register', methods=['POST'])
@ratelimit
def register():
    data = request.get_json()
    
    if not data:
        return error_response('A kérés törzse kötelező', 400)
    
    username = data.get('username', '').strip() if isinstance(data.get('username'), str) else ''
    email = data.get('email', '').strip() if isinstance(data.get('email'), str) else ''
    password = data.get('password', '')
    
    if not username:
        return error_response('A felhasználónév kötelező', 400)
    if not email:
        return error_response('Az e-mail kötelező', 400)
    if not password:
        return error_response('A jelszó kötelező', 400)
    
    if not validate_username(username):
        return error_response('A felhasználónév 3–80 karakter hosszú legyen, és csak betűket, számokat vagy aláhúzásjelet tartalmazhat', 400)
    
    if not validate_email(email):
        return error_response('Érvénytelen e-mail formátum', 400)
    
    if not validate_password(password):
        return error_response('A jelszónak legalább 8 karakter hosszúnak kell lennie, és tartalmaznia kell nagy- és kisbetűt, valamint számot', 400)
    
    existing_user = User.query.filter(
        (User.username == username) | (User.email == email)
    ).first()
    
    if existing_user:
        if existing_user.username == username:
            return error_response('A felhasználónév már létezik', 409)
        if existing_user.email == email:
            return error_response('Az e-mail már létezik', 409)
    
    try:
        password_hash = hash_password(password)
        verification_token = generate_verification_token()
        verification_expires = get_verification_expiry()
        
        from app.utils import generate_unique_id
        for _ in range(5):
            try:
                new_user = User(
                    id=generate_unique_id(),
                    username=username,
                    email=email,
                    password_hash=password_hash,
                    world_ids=[],
                    settings={},
                    email_verified=not EmailConfig.REQUIRE_EMAIL_VERIFICATION,
                    verification_token=verification_token,
                    verification_token_expires=verification_expires
                )
                db.session.add(new_user)
                db.session.commit()
                send_verification_email(email, username, verification_token)
                if EmailConfig.REQUIRE_EMAIL_VERIFICATION:
                    return success_response({
                        'message': 'Regisztráció sikeres. Kérjük, ellenőrizd az e-mail fiókodat a megerősítéshez.',
                        'user': {
                            'id': new_user.id,
                            'username': new_user.username,
                            'email': new_user.email,
                            'email_verified': new_user.email_verified
                        },
                        'requires_verification': True
                    }, 201)
                else:
                    from flask import current_app
                    token = generate_token(new_user.id, current_app.config['SECRET_KEY'])
                    return success_response({
                        'message': 'Regisztráció sikeres.',
                        'user': new_user.to_dict(),
                        'token': token,
                        'requires_verification': False
                    }, 201)
            except IntegrityError:
                db.session.rollback()
                continue
        return error_response('Nem sikerült egyedi azonosítót generálni, próbáld újra később.', 500)
    except IntegrityError:
        db.session.rollback()
        return error_response('A felhasználó már létezik', 409)
    except Exception as e:
        db.session.rollback()
        return error_response('A felhasználó létrehozása sikertelen', 500)


@api.route('/login', methods=['POST'])
@ratelimit
def login():
    data = request.get_json()
    
    if not data:
        return error_response('A kérés törzse kötelező', 400)
    
    username_or_email = data.get('username', '').strip() if isinstance(data.get('username'), str) else ''
    password = data.get('password', '')
    
    if not username_or_email:
        return error_response('Felhasználónév vagy e-mail szükséges', 400)
    if not password:
        return error_response('A jelszó kötelező', 400)
    
    user = User.query.filter(
        (User.username == username_or_email) | (User.email == username_or_email)
    ).first()
    
    if not user:
        return error_response('Érvénytelen hitelesítő adatok', 401)
    
    if not verify_password(password, user.password_hash):
        return error_response('Érvénytelen hitelesítő adatok', 401)
    
    if EmailConfig.REQUIRE_EMAIL_VERIFICATION:
        if not user.email_verified:
            verification_token = generate_verification_token()
            verification_expires = get_verification_expiry()
            user.verification_token = verification_token
            user.verification_token_expires = verification_expires
            db.session.commit()
            
            send_verification_email(user.email, user.username, verification_token)
            return error_response('Az e-mail cím még nincs megerősítve. Új megerősítő e-mailt küldtünk.', 403)
        
        login_token = generate_verification_token()
        login_token_expires = get_verification_expiry()
        user.login_verification_token = login_token
        user.login_verification_token_expires = login_token_expires
        db.session.commit()
        
        send_login_verification_email(user.email, user.username, login_token)
        
        return success_response({
            'message': 'Bejelentkezési megerősítő e-mailt küldtünk. Kérjük, ellenőrizd az e-mail fiókodat.',
            'requires_verification': True
        })
    else:
        login_token = generate_verification_token()
        login_token_expires = get_verification_expiry()
        user.login_verification_token = login_token
        user.login_verification_token_expires = login_token_expires
        db.session.commit()
        
        send_login_verification_email(user.email, user.username, login_token)
        
        from flask import current_app
        token = generate_token(user.id, current_app.config['SECRET_KEY'])
        
        return success_response({
            'message': 'Bejelentkezés sikeres.',
            'user': user.to_dict(),
            'token': token,
            'requires_verification': False
        })


@api.route('/account', methods=['DELETE'])
@ratelimit
def delete_account():
    from flask import current_app
    
    auth_header = request.headers.get('Authorization')
    if not auth_header:
        return error_response('Az Authorization fejléc hiányzik', 401)
    
    parts = auth_header.split()
    if len(parts) != 2 or parts[0].lower() != 'bearer':
        return error_response('Érvénytelen Authorization fejléc formátum', 401)
    
    token = parts[1]
    from app.utils import decode_token
    payload = decode_token(token, current_app.config['SECRET_KEY'])
    
    if not payload:
        return error_response('Érvénytelen vagy lejárt token', 401)
    
    user_id = payload.get('user_id')
    user = User.query.get(user_id)
    
    if not user:
        return error_response('Felhasználó nem található', 404)
    
    data = request.get_json()
    if not data:
        return error_response('A kérés törzse kötelező', 400)
    
    password = data.get('password', '')
    if not password:
        return error_response('A fiók törléséhez jelszó szükséges', 400)
    
    if not verify_password(password, user.password_hash):
        return error_response('Érvénytelen jelszó', 401)
    
    try:
        db.session.delete(user)
        db.session.commit()
        return success_response({'message': 'A fiók sikeresen törölve'})
    except Exception as e:
        db.session.rollback()
        return error_response('A fiók törlése sikertelen', 500)


@api.route('/verify-email', methods=['POST'])
@ratelimit
def verify_email():
    data = request.get_json()
    
    if not data:
        return error_response('A kérés törzse kötelező', 400)
    
    token = data.get('token', '')
    
    if not token:
        return error_response('A megerősítő token kötelező', 400)
    
    user = User.query.filter_by(verification_token=token).first()
    
    if not user:
        return error_response('Érvénytelen megerősítő token', 400)
    
    if user.verification_token_expires < datetime.utcnow():
        return error_response('A megerősítő token lejárt', 400)
    
    user.email_verified = True
    user.verification_token = None
    user.verification_token_expires = None
    db.session.commit()
    
    from flask import current_app
    access_token = generate_token(user.id, current_app.config['SECRET_KEY'])
    
    return success_response({
        'message': 'E-mail cím sikeresen megerősítve',
        'user': user.to_dict(),
        'token': access_token
    })


@api.route('/verify-login', methods=['POST'])
@ratelimit
def verify_login():
    data = request.get_json()
    
    if not data:
        return error_response('A kérés törzse kötelező', 400)
    
    token = data.get('token', '')
    
    if not token:
        return error_response('A megerősítő token kötelező', 400)
    
    user = User.query.filter_by(login_verification_token=token).first()
    
    if not user:
        return error_response('Érvénytelen bejelentkezési token', 400)
    
    if user.login_verification_token_expires < datetime.utcnow():
        return error_response('A bejelentkezési token lejárt', 400)
    
    user.login_verification_token = None
    user.login_verification_token_expires = None
    db.session.commit()
    
    from flask import current_app
    access_token = generate_token(user.id, current_app.config['SECRET_KEY'])
    
    return success_response({
        'message': 'Bejelentkezés sikeresen megerősítve',
        'user': user.to_dict(),
        'token': access_token
    })


@api.route('/resend-verification', methods=['POST'])
@ratelimit
def resend_verification():
    data = request.get_json()
    
    if not data:
        return error_response('A kérés törzse kötelező', 400)
    
    email = data.get('email', '').strip() if isinstance(data.get('email'), str) else ''
    
    if not email:
        return error_response('Az e-mail kötelező', 400)
    
    user = User.query.filter_by(email=email).first()
    
    if not user:
        return error_response('Felhasználó nem található', 404)
    
    if user.email_verified:
        return error_response('Az e-mail cím már megerősítve van', 400)
    
    verification_token = generate_verification_token()
    verification_expires = get_verification_expiry()
    user.verification_token = verification_token
    user.verification_token_expires = verification_expires
    db.session.commit()
    
    send_verification_email(user.email, user.username, verification_token)
    
    return success_response({
        'message': 'Új megerősítő e-mailt küldtünk'
    })


@api.route('/create/world', methods=['POST'])
@ratelimit
@require_auth
def create_world():
    data = request.get_json()
    
    if not data:
        return error_response('A kérés törzse kötelező', 400)
    
    name = data.get('name', '').strip() if isinstance(data.get('name'), str) else ''
    
    if not name:
        return error_response('A világ neve kötelező', 400)
    
    try:
        for _ in range(5):
            try:
                new_world = World(
                    world_id=generate_unique_id(),
                    name=name
                )
                db.session.add(new_world)
                db.session.commit()
                return success_response({
                    'message': 'Világ sikeresen létrehozva',
                    'world': new_world.to_dict()
                }, 201)
            except IntegrityError:
                db.session.rollback()
                continue
        return error_response('Nem sikerült egyedi azonosítót generálni', 500)
    except Exception as e:
        db.session.rollback()
        return error_response('A világ létrehozása sikertelen', 500)


@api.route('/create/card', methods=['POST'])
@ratelimit
@require_auth
def create_card():
    data = request.get_json()
    
    if not data:
        return error_response('A kérés törzse kötelező', 400)
    
    try:
        world_id = data.get('world_id', '0') if isinstance(data.get('world_id', '0'), str) else str(data.get('world_id', '0'))
        user_id = data.get('user_id', '0') if isinstance(data.get('user_id', '0'), str) else str(data.get('user_id', '0'))
        name = data.get('name', '0') if isinstance(data.get('name', '0'), str) else str(data.get('name', '0'))
        card_type = data.get('type', '0') if isinstance(data.get('type', '0'), str) else str(data.get('type', '0'))
        picture_val = data.get('picture', None)
        if isinstance(picture_val, str):
            picture_bytes = picture_val.encode('utf-8')
        else:
            picture_bytes = None
        
        def to_int(v, default=0):
            try:
                return int(v)
            except Exception:
                return default
        
        def to_bool(v, default=False):
            if isinstance(v, bool):
                return v
            if isinstance(v, int):
                return v != 0
            if isinstance(v, str):
                return v.strip().lower() not in ('', '0', 'false', 'no', 'off')
            return default
        
        health = to_int(data.get('health', 0), 0)
        damage = to_int(data.get('damage', 0), 0)
        position = to_int(data.get('position', 0), 0)
        is_leader = to_bool(data.get('is_leader', 0), False)

        for _ in range(5):
            try:
                new_card = Card(
                    id=generate_unique_id(),
                    world_id=world_id,
                    owner_id=user_id,
                    name=name,
                    picture=picture_bytes,
                    health=health,
                    damage=damage,
                    type=card_type,
                    position=position,
                    is_leader=is_leader,
                )
                db.session.add(new_card)
                db.session.commit()
                return success_response({
                    'message': 'Kártya sikeresen létrehozva',
                    'card': new_card.to_dict()
                }, 201)
            except IntegrityError:
                db.session.rollback()
                continue
        return error_response('Nem sikerült egyedi azonosítót generálni', 500)
    except Exception as e:
        db.session.rollback()
        return error_response('A kártya létrehozása sikertelen', 500)
@api.route('/create/dungeon', methods=['POST'])
@ratelimit
@require_auth
def create_dungeon():
    data = request.get_json()
    if not data:
        return error_response('A kérés törzse kötelező', 400)
    name = data.get('name', '').strip() if isinstance(data.get('name'), str) else ''
    world_id = data.get('world_id')
    list_ids = data.get('list_of_cards_ids', [])
    if not name:
        return error_response('A dungeon neve kötelező', 400)
    if world_id is None:
        return error_response('A világ azonosítója kötelező', 400)
    try:
        world_id = str(world_id)
    except Exception:
        return error_response('A világ azonosítónak egész számnak kell lennie', 400)
    if not isinstance(list_ids, list):
        return error_response('A list_of_cards_ids-nak listának kell lennie', 400)
    try:
        for _ in range(5):
            try:
                new_dungeon = Dungeon(
                    id=generate_unique_id(),
                    name=name,
                    world_id=str(world_id).strip(),
                    list_of_card_ids=list_ids
                )
                db.session.add(new_dungeon)
                db.session.commit()
                return success_response({
                    'message': 'Dungeon sikeresen létrehozva',
                    'dungeon': new_dungeon.to_dict()
                }, 201)
            except IntegrityError:
                db.session.rollback()
                continue
        return error_response('Nem sikerült egyedi azonosítót generálni', 500)
    except Exception as e:
        db.session.rollback()
        return error_response('A dungeon létrehozása sikertelen', 500)

@api.route('/health', methods=['GET'])
@ratelimit
def health_check():
    return success_response({'status': 'egészséges'})

@api.errorhandler(404)
def not_found(error):
    return error_response('Erőforrás nem található', 404)


@api.errorhandler(500)
def internal_error(error):
    return error_response('Belső szerverhiba', 500)
