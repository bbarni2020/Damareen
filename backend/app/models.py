from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()


class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.String(32), primary_key=True, unique=True, nullable=False)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    world_ids = db.Column(db.JSON, nullable=True, default=list)
    settings = db.Column(db.JSON, nullable=True, default=dict)
    email_verified = db.Column(db.Boolean, default=False, nullable=False)
    verification_token = db.Column(db.String(256), nullable=True)
    verification_token_expires = db.Column(db.DateTime, nullable=True)
    login_verification_token = db.Column(db.String(256), nullable=True)
    login_verification_token_expires = db.Column(db.DateTime, nullable=True)
    password_reset_token = db.Column(db.String(256), nullable=True)
    password_reset_token_expires = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'world_ids': self.world_ids,
            'settings': self.settings,
            'email_verified': self.email_verified,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    def __repr__(self):
        return f'<User {self.username}>'


class Card(db.Model):
    __tablename__ = 'cards'

    id = db.Column(db.String(32), primary_key=True, unique=True, nullable=False)
    world_id = db.Column(db.String(32), nullable=False)
    owner_id = db.Column(db.String(32), nullable=False)
    name = db.Column(db.String(16), nullable=False)
    picture = db.Column(db.LargeBinary, nullable=True)
    health = db.Column(db.Integer, nullable=False)
    damage = db.Column(db.Integer, nullable=False)
    type = db.Column(db.String(6), nullable=False)
    position = db.Column(db.Integer, nullable=False)
    is_leader = db.Column(db.String(32), nullable=False)

    def to_dict(self):
        return {
            'id': self.id,
            'world_id': self.world_id,
            'owner_id': self.owner_id,
            'name': self.name,
            'picture': self.picture.decode('utf-8') if self.picture else None,
            'health': self.health,
            'damage': self.damage,
            'type': self.type,
            'position': self.position,
            'is_leader': self.is_leader,
        }
    
    def __repr__(self):
        return f'<Card {self.name} - World {self.world_id}>'


class World(db.Model):
    __tablename__ = 'worlds'

    world_id = db.Column(db.String(32), primary_key=True, unique=True, nullable=False)
    name = db.Column(db.String(120), nullable=False)
    
    def to_dict(self):
        return {
            'world_id': self.world_id,
            'name': self.name
        }
    
    def __repr__(self):
        return f'<World {self.name}>'


class Dungeon(db.Model):
    __tablename__ = 'dungeons'
    
    id = db.Column(db.String(32), primary_key=True, unique=True, nullable=False)
    name = db.Column(db.String(120), nullable=False)
    world_id = db.Column(db.String(32), nullable=False)
    list_of_card_ids = db.Column(db.JSON, nullable=True, default=list)
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'world_id': self.world_id,
            'list_of_card_ids': self.list_of_card_ids,
        }
    
    def __repr__(self):
        return f'<Dungeon {self.name} - World {self.world_id}>'
