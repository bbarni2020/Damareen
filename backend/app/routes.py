from flask import Blueprint, jsonify, request
import time
import random
from functools import wraps
from datetime import datetime, timedelta
from app.models import db, User, World, Card, Dungeon
from app.utils import (
    success_response, error_response, validate_email, 
    validate_username, validate_password, hash_password,
    verify_password, generate_token, require_auth, generate_unique_id,
    require_master, is_master_of_world, check_master_status
)
from app.email_service import (
    send_verification_email, send_login_notification_email,
    generate_verification_token, get_verification_expiry,
    send_password_reset_email
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


@api.route('/user/register', methods=['POST'])
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


@api.route('/user/login', methods=['POST'])
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
    
    from flask import current_app
    token = generate_token(user.id, current_app.config['SECRET_KEY'])
    
    send_login_notification_email(user.email, user.username)
    
    return success_response({
        'message': 'Bejelentkezés sikeres.',
        'user': user.to_dict(),
        'token': token
    })


@api.route('/user/delete', methods=['DELETE'])
@ratelimit
@require_auth
def delete_account():
    user = request.current_user
    
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


@api.route('/user', methods=['GET'])
@ratelimit
@require_auth
def get_user():
    user = request.current_user
    
    return success_response({
        'username': user.username,
        'email': user.email,
        'settings': user.settings or {}
    })


@api.route('/user/password-reset', methods=['POST'])
@ratelimit
def request_password_reset():
    data = request.get_json()
    
    if not data:
        return error_response('A kérés törzse kötelező', 400)
    
    email = data.get('email', '').strip() if isinstance(data.get('email'), str) else ''
    
    if not email:
        return error_response('Az e-mail kötelező', 400)
    
    user = User.query.filter_by(email=email).first()
    
    if not user:
        return success_response({
            'message': 'Ha az e-mail cím regisztrálva van, jelszó visszaállítási linket küldtünk rá'
        })
    
    reset_token = generate_verification_token()
    reset_expires = datetime.utcnow() + timedelta(hours=1)
    user.password_reset_token = reset_token
    user.password_reset_token_expires = reset_expires
    db.session.commit()
    
    send_password_reset_email(user.email, user.username, reset_token)
    
    return success_response({
        'message': 'Ha az e-mail cím regisztrálva van, jelszó visszaállítási linket küldtünk rá'
    })


@api.route('/user/password-reset', methods=['PUT'])
@ratelimit
def reset_password():
    data = request.get_json()
    
    if not data:
        return error_response('A kérés törzse kötelező', 400)
    
    token = data.get('token', '')
    new_password = data.get('password', '')
    
    if not token:
        return error_response('A visszaállítási token kötelező', 400)
    
    if not new_password:
        return error_response('Az új jelszó kötelező', 400)
    
    if not validate_password(new_password):
        return error_response('A jelszónak legalább 8 karakter hosszúnak kell lennie, és tartalmaznia kell nagy- és kisbetűt, valamint számot', 400)
    
    user = User.query.filter_by(password_reset_token=token).first()
    
    if not user:
        return error_response('Érvénytelen visszaállítási token', 400)
    
    if user.password_reset_token_expires < datetime.utcnow():
        return error_response('A visszaállítási token lejárt', 400)
    
    user.password_hash = hash_password(new_password)
    user.password_reset_token = None
    user.password_reset_token_expires = None
    db.session.commit()
    
    return success_response({
        'message': 'A jelszó sikeresen megváltoztatva'
    })


@api.route('/user/verify-email', methods=['POST'])
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


@api.route('/user/resend-verification', methods=['POST'])
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
    user_id = data.get('user_id', '').strip() if isinstance(data.get('user_id'), str) else ''
    is_master = True
    
    if not name:
        return error_response('A világ neve kötelező', 400)
    
    if not user_id:
        return error_response('A felhasználó azonosítója kötelező', 400)
    
    user = User.query.get(user_id)
    if not user:
        return error_response('Felhasználó nem található', 404)
    
    try:
        for _ in range(5):
            try:
                new_world = World(
                    world_id=generate_unique_id(),
                    name=name
                )
                db.session.add(new_world)
                db.session.flush()
                
                if not isinstance(user.world_ids, dict):
                    user.world_ids = {}
                
                updated_worlds = dict(user.world_ids)
                updated_worlds[new_world.world_id] = is_master
                user.world_ids = updated_worlds
                
                from sqlalchemy.orm.attributes import flag_modified
                flag_modified(user, 'world_ids')
                
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
@require_master
def create_card():
    user = request.current_user
    
    data = request.get_json()
    
    if not data:
        return error_response('A kérés törzse kötelező', 400)
    
    try:
        world_id = data.get('world_id', '0') if isinstance(data.get('world_id', '0'), str) else str(data.get('world_id', '0'))
        user_id = user.id
        name = data.get('name', '0') if isinstance(data.get('name', '0'), str) else str(data.get('name', '0'))
        raw_type = data.get('type', '')
        if isinstance(raw_type, str):
            card_type = raw_type.strip().lower()
        else:
            card_type = str(raw_type).strip().lower()

        if card_type not in ('t', 'f', 'v', 'l'):
            return error_response('Érvénytelen típus. Csak a következők engedélyezettek: t, f, v, l', 400)
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
        def is_whole_number(v):
            if isinstance(v, int):
                return True
            if isinstance(v, float):
                return v.is_integer()
            if isinstance(v, str):
                s = v.strip()
                if s == '':
                    return False
                if s.lstrip('-').isdigit():
                    return True
            try:
                f = float(s)
            except Exception:
                return False
            return f.is_integer()
            return False

        raw_health = data.get('health', 0)
        if not is_whole_number(raw_health):
            return error_response('Az életerőnek egész számnak kell lennie', 400)
        health = to_int(raw_health, 0)
        if not (1 <= health <= 100):
            return error_response('Az életerőnek 1 és 100 között kell lennie', 400)

        raw_damage = data.get('damage', 0)
        if not is_whole_number(raw_damage):
            return error_response('A sebzésnek egész számnak kell lennie', 400)
        damage = to_int(raw_damage, 0)
        if not (2 <= damage <= 100):
            return error_response('A sebzésnek 2 és 100 között kell lennie', 400)
        position = to_int(0)
        is_leader = ""

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
@require_master
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
    
    if len(list_ids) not in [1, 4, 6]:
        return error_response('A kazamata 1, 4 vagy 6 kártyából kell álljon', 400)
    
    if list_ids:
        cards = Card.query.filter(Card.id.in_(list_ids)).all()
        card_dict = {card.id: card for card in cards}
        
        if len(card_dict) != len(list_ids):
            return error_response('Egy vagy több kártya azonosító nem található', 404)
        
        ordered_cards = [card_dict[card_id] for card_id in list_ids]
        
        if len(list_ids) == 1:

            if ordered_cards[0].is_leader != "":
                return error_response('Az egyszerű találkozás típusú kazamatában csak sima kártya lehet', 400)
        
        elif len(list_ids) in [4, 6]:
            if ordered_cards[-1].is_leader == "":
                return error_response('A kazamata utolsó kártyája vezér kell legyen', 400)
            
            
            for i in range(len(ordered_cards) - 1):
                if ordered_cards[i].is_leader != "":
                    return error_response('A kazamata kártyái közül csak az utolsó lehet vezér', 400)
        
        try:
            for position, card_id in enumerate(list_ids):
                card = card_dict[card_id]
                card.position = position + 1
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            return error_response('A kártyák pozíciójának frissítése sikertelen', 500)
    
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

@api.route('/create/collection', methods=['POST'])
@ratelimit
@require_auth
@require_master
def create_collection():
    data = request.get_json()
    
    if not data:
        return error_response('A kérés törzse kötelező', 400)
    
    owner_id = data.get('owner_id', '').strip() if isinstance(data.get('owner_id'), str) else ''
    list_of_cards_ids = data.get('list_of_cards_ids', [])
    
    if not owner_id:
        return error_response('A tulajdonos azonosítója kötelező', 400)
    
    if not isinstance(list_of_cards_ids, list):
        return error_response('A list_of_cards_ids listának kell lennie', 400)
    
    if not list_of_cards_ids:
        return error_response('A list_of_cards_ids nem lehet üres', 400)
    
    try:
        original_cards = Card.query.filter(Card.id.in_(list_of_cards_ids)).all()
        
        if not original_cards:
            return error_response('Nem található kártya a megadott azonosítókkal', 404)
        
        duplicated_cards = []
        
        for original_card in original_cards:
            success = False
            for _ in range(5):
                try:
                    new_card = Card(
                        id=generate_unique_id(),
                        world_id=original_card.world_id,
                        owner_id=owner_id,
                        name=original_card.name,
                        picture=original_card.picture,
                        health=original_card.health,
                        damage=original_card.damage,
                        type=original_card.type,
                        position=original_card.position,
                        is_leader=original_card.is_leader
                    )
                    db.session.add(new_card)
                    db.session.flush()
                    duplicated_cards.append(new_card)
                    success = True
                    break
                except IntegrityError:
                    db.session.rollback()
                    continue
            
            if not success:
                db.session.rollback()
                return error_response('Nem sikerült egyedi azonosítót generálni a kártyához', 500)
        
        db.session.commit()
        
        return success_response({
            'message': 'Kollekció sikeresen létrehozva',
            'duplicated_cards': [card.to_dict() for card in duplicated_cards],
            'count': len(duplicated_cards)
        }, 201)
    except Exception as e:
        db.session.rollback()
        return error_response('A kollekció létrehozása sikertelen', 500)

@api.route('/create/leader', methods=['POST'])
@ratelimit
@require_auth
@require_master
def create_leader():
    data = request.get_json()
    
    if not data:
        return error_response('A kérés törzse kötelező', 400)
    
    card_id = data.get('card_id', '').strip() if isinstance(data.get('card_id'), str) else ''
    damage_doubled = data.get('damage_doubled')
    
    if not card_id:
        return error_response('A kártya azonosítója kötelező', 400)
    
    if not isinstance(damage_doubled, bool):
        return error_response('A damage_doubled értéknek boolean-nak kell lennie', 400)
    
    try:
        original_card = Card.query.get(card_id)
        
        if not original_card:
            return error_response('Nem található kártya a megadott azonosítóval', 404)
        
        new_damage = original_card.damage
        new_health = original_card.health
        
        if damage_doubled:
            new_damage = original_card.damage * 2
        else:
            new_health = original_card.health * 2
        
        for _ in range(5):
            try:
                new_leader = Card(
                    id=generate_unique_id(),
                    world_id=original_card.world_id,
                    owner_id=original_card.owner_id,
                    name=original_card.name,
                    picture=original_card.picture,
                    health=new_health,
                    damage=new_damage,
                    type=original_card.type,
                    position=original_card.position,
                    is_leader=original_card.id
                )
                db.session.add(new_leader)
                db.session.commit()
                
                return success_response({
                    'message': 'Vezér sikeresen létrehozva',
                    'leader': new_leader.to_dict()
                }, 201)
            except IntegrityError:
                db.session.rollback()
                continue
        
        return error_response('Nem sikerült egyedi azonosítót generálni', 500)
    except Exception as e:
        db.session.rollback()
        return error_response('A vezér létrehozása sikertelen', 500)
    
@api.route('/deck', methods=['POST'])
@ratelimit
@require_auth
def set_deck():
    user = request.current_user
    data = request.get_json()
    if not data:
        return error_response('A kérés törzse kötelező', 400)
    cards_list = data.get('cards') or data.get('card_ids') or []
    if not isinstance(cards_list, list):
        return error_response('A kártyák listájának listának kell lennie', 400)
    cards_list = [str(x).strip() for x in cards_list if str(x).strip()]
    if len(cards_list) not in (1, 4, 6):
        return error_response('Pontosan 1, 4 vagy 6 kártyát kell megadni', 400)
    if len(set(cards_list)) != len(cards_list):
        return error_response('Ismétlődő kártya azonosítók', 400)
    cards = Card.query.filter(Card.id.in_(cards_list)).all()
    if len(cards) != len(cards_list):
        return error_response('Nem található kártya a megadott azonosítókkal', 404)
    for c in cards:
        if c.owner_id != user.id:
            return error_response('Csak a saját kártyáidat állíthatod be paklinak', 403)
    pos_map = {cid: i + 1 for i, cid in enumerate(cards_list)}
    try:
        for c in cards:
            c.position = pos_map.get(c.id, c.position)
        db.session.commit()
        cards_by_id = {c.id: c for c in cards}
        ordered = [cards_by_id[cid].to_dict() for cid in cards_list]
        return success_response({'message': 'Pakli frissítve', 'cards': ordered})
    except Exception:
        db.session.rollback()
        return error_response('A pakli frissítése sikertelen', 500)

@api.route('/game/join', methods=['POST'])
@ratelimit
@require_auth
def join_game():
    user = request.current_user
    
    data = request.get_json()
    
    if not data:
        return error_response('A kérés törzse kötelező', 400)
    
    invite_code = data.get('invite_code', '').strip() if isinstance(data.get('invite_code'), str) else ''
    
    if not invite_code:
        return error_response('A meghívó kód kötelező', 400)
    
    world = World.query.filter_by(world_id=invite_code).first()
    
    if not world:
        return error_response('A világ nem található', 404)
    
    if not isinstance(user.world_ids, dict):
        user.world_ids = {}
    
    if invite_code in user.world_ids:
        return error_response('Már csatlakoztál ehhez a világhoz', 409)
    
    try:
        user.world_ids[invite_code] = False
        db.session.commit()
        
        return success_response({
            'message': 'Sikeresen csatlakoztál a világhoz',
            'world': world.to_dict()
        })
    except Exception as e:
        print(e)
        db.session.rollback()
        return error_response('A csatlakozás sikertelen', 500)


@api.route('/game/dungeon', methods=['GET'])
@ratelimit
@require_auth
def get_game_dungeon():
    world_id = request.args.get('world_id')
    
    if not world_id:
        return error_response('A világ azonosítója kötelező', 400)
    
    dungeons = Dungeon.query.filter_by(world_id=str(world_id)).all()
    
    if len(dungeons) == 0:
        return error_response('A játékmester még nem hozott létre kazamatát ebben a világban', 404)
    
    if len(dungeons) == 1:
        selected_dungeons = dungeons
    else:
        selected_dungeons = random.sample(dungeons, min(2, len(dungeons)))
    
    result = [
        {
            'id': dungeon.id,
            'number_of_cards': len(dungeon.list_of_card_ids)
        }
        for dungeon in selected_dungeons
    ]
    
    return success_response({'dungeons': result})


@api.route('/user/is-master', methods=['GET'])
@ratelimit
@require_auth
def is_master():
    return check_master_status()


@api.route('/user/list/worlds', methods=['GET'])
@ratelimit
@require_auth
def list_user_worlds():
    user = request.current_user
    
    
    all_worlds = World.query.all()
    worlds_dict = {w.world_id: w.name for w in all_worlds}
    
    user_world_map = user.world_ids or {}
    where_user_is_master = []
    already_joined_worlds = {}
    
    if isinstance(user_world_map, dict):
        for world_id, is_master in user_world_map.items():
            already_joined_worlds[world_id] = worlds_dict.get(world_id, world_id)
            if is_master is True:
                where_user_is_master.append(world_id)
    
    return success_response({
        'worlds': worlds_dict,
        'where_user_is_master': where_user_is_master,
        'already_joined_worlds': already_joined_worlds
    })
@api.route('/world/list/dungeons', methods=['GET'])
@ratelimit
@require_auth
@require_master
def list_world_dungeons():
    world_id = request.args.get('world_id')
    if not world_id:
        return error_response('A világ azonosítója kötelező', 400)
    dungeons = Dungeon.query.filter_by(world_id=world_id).all()
    return success_response({'dungeons': [d.to_dict() for d in dungeons]})


@api.route('/world/list/cards', methods=['GET'])
@ratelimit
@require_auth
@require_master
def list_world_cards():
    world_id = request.args.get('world_id')
    if not world_id:
        return error_response('A világ azonosítója kötelező', 400)
    cards = Card.query.filter_by(world_id=world_id).all()
    return success_response({'cards': [c.to_dict() for c in cards]})


@api.route('/world/list/users', methods=['GET'])
@ratelimit
@require_auth
@require_master
def list_world_users():
    current_user = request.current_user
    world_id = request.args.get('world_id')
    if not world_id:
        return error_response('A világ azonosítója kötelező', 400)
    users = User.query.all()
    result = []
    for u in users:
        if u.id == current_user.id:
            continue
        wm = u.world_ids or {}
        if isinstance(wm, dict) and str(world_id) in wm:
            result.append({
                'id': u.id,
                'username': u.username,
                'is_master': bool(wm.get(str(world_id)))
            })
    return success_response({'users': result})


@api.route('/delete/world', methods=['DELETE'])
@ratelimit
@require_auth
@require_master
def delete_world():
    data = request.get_json()
    
    if not data:
        return error_response('A kérés törzse kötelező', 400)
    
    world_id = data.get('world_id', '').strip() if isinstance(data.get('world_id'), str) else ''
    
    if not world_id:
        return error_response('A világ azonosítója kötelező', 400)
    
    world = World.query.get(world_id)
    
    if not world:
        return error_response('A világ nem található', 404)
    
    try:
        Card.query.filter_by(world_id=world_id).delete()
        Dungeon.query.filter_by(world_id=world_id).delete()
        
        users = User.query.all()
        for user in users:
            if user.world_ids and world_id in user.world_ids:
                del user.world_ids[world_id]
                user.world_ids = dict(user.world_ids)
        
        db.session.delete(world)
        db.session.commit()
        
        return success_response({
            'message': 'A világ sikeresen törölve'
        })
    except Exception as e:
        db.session.rollback()
        return error_response('A világ törlése sikertelen', 500)


@api.route('/delete/dungeon', methods=['DELETE'])
@ratelimit
@require_auth
@require_master
def delete_dungeon():
    data = request.get_json()
    
    if not data:
        return error_response('A kérés törzse kötelező', 400)
    
    dungeon_id = data.get('dungeon_id', '').strip() if isinstance(data.get('dungeon_id'), str) else ''
    world_id = data.get('world_id', '').strip() if isinstance(data.get('world_id'), str) else ''
    
    if not dungeon_id:
        return error_response('A dungeon azonosítója kötelező', 400)
    if not world_id:
        return error_response('A világ azonosítója kötelező', 400)
    
    dungeon = Dungeon.query.filter_by(id=dungeon_id, world_id=world_id).first()
    if not dungeon:
        return error_response('Dungeon nem található', 404)
    
    try:
        db.session.delete(dungeon)
        db.session.commit()
        return success_response({'message': 'Dungeon sikeresen törölve'})
    except Exception as e:
        db.session.rollback()
        return error_response('A dungeon törlése sikertelen', 500)

@api.route('/game/fight', methods=['GET'])
@ratelimit
@require_auth
def fight():
    user = request.current_user
    dungeon_id = request.args.get('dungeon_id')
    if not dungeon_id:
        return error_response('A dungeon azonosítója kötelező', 400)
    dungeon = Dungeon.query.filter_by(id=str(dungeon_id)).first()
    if not dungeon:
        return error_response('Dungeon nem található', 404)
    dungeon_card_ids = dungeon.list_of_card_ids or []
    dungeon_cards = []
    if dungeon_card_ids:
        cards = Card.query.filter(Card.id.in_(dungeon_card_ids)).all()
        card_map = {c.id: c for c in cards}
        for cid in dungeon_card_ids:
            if cid in card_map:
                dungeon_cards.append(card_map[cid].to_dict())
    player_cards = Card.query.filter(Card.owner_id == user.id, Card.position != 0).order_by(Card.position).all()
    player_deck = []
    for idx, c in enumerate(player_cards):
        d = c.to_dict()
        d['position'] = idx + 1
        player_deck.append(d)

    battles = []
    beats = {'t': 'f', 'f': 'v', 'v': 'l', 'l': 't'}
    pairs = min(len(dungeon_cards), len(player_deck))
    for i in range(pairs):
        dc = dungeon_cards[i]
        pc = player_deck[i]
        try:
            p_damage = int(pc.get('damage', 0))
        except Exception:
            p_damage = 0
        try:
            d_damage = int(dc.get('damage', 0))
        except Exception:
            d_damage = 0
        try:
            p_health = int(pc.get('health', 0))
        except Exception:
            p_health = 0
        try:
            d_health = int(dc.get('health', 0))
        except Exception:
            d_health = 0

        p_can_kill = p_damage > d_health
        d_can_kill = d_damage > p_health

        winner = None
        reason = None
        if p_can_kill and not d_can_kill:
            winner = 'player'
            reason = 'damage'
        elif d_can_kill and not p_can_kill:
            winner = 'dungeon'
            reason = 'damage'
        else:
            p_type = (pc.get('type') or '').lower()
            d_type = (dc.get('type') or '').lower()
            if p_type and d_type and p_type != d_type:
                if beats.get(p_type) == d_type:
                    winner = 'player'
                    reason = 'type'
                elif beats.get(d_type) == p_type:
                    winner = 'dungeon'
                    reason = 'type'
                else:
                    winner = 'dungeon'
                    reason = 'dungeon_fallback'
            else:
                winner = 'dungeon'
                reason = 'dungeon_fallback'

        battles.append({
            'position': i + 1,
            'player_card': pc,
            'dungeon_card': dc,
            'winner': winner,
            'reason': reason
        })

    player_wins = sum(1 for b in battles if b.get('winner') == 'player')
    dungeon_wins = sum(1 for b in battles if b.get('winner') == 'dungeon')
    winner = 'player' if player_wins >= dungeon_wins else 'dungeon'

    return success_response({
        'winner': winner,
        'battles': battles
    })

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
