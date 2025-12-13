from flask import Flask
from flask_cors import CORS
from config import Config
import os


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    frontend_url = os.environ.get('FRONTEND_URL', 'http://localhost:3000')
    
    CORS(app, resources={
        r"/*": {
            "origins": [
                frontend_url,
                "http://localhost:3000",
                "http://127.0.0.1:3000",
                "http://localhost:7621",
                "http://127.0.0.1:7621",
                "http://localhost:5500",
                "http://127.0.0.1:5500",
                "https://damareen.bbarni.hackclub.app",
                "https://api.damareen.bbarni.hackclub.app",
            ],
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization"],
            "supports_credentials": True,  # cookie-k miatt kell
        }
    })
    
    # API Blueprint regisztrálása
    from app.routes import api
    app.register_blueprint(api)
    
    return app
