from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()


class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
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


class Game(db.Model):
    __tablename__ = 'games'
    
    id = db.Column(db.Integer, primary_key=True)
    player_id = db.Column(db.Integer, nullable=False)
    card_ids = db.Column(db.JSON, nullable=True, default=list)
    player_won = db.Column(db.Boolean, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    def to_dict(self):
        return {
            'id': self.id,
            'player_id': self.player_id,
            'card_ids': self.card_ids,
            'player_won': self.player_won,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    def __repr__(self):
        return f'<Game {self.id} - Player {self.player_id}>'
