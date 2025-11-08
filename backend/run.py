import os
from dotenv import load_dotenv
from app import create_app
from app.models import db

load_dotenv()  # pull in FLASK_ENV, PORT, etc. from a local .env if present

app = create_app()

with app.app_context():
    db.init_app(app)
    db.create_all()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 7621))
    env = os.environ.get('FLASK_ENV', 'development')
    if env == 'production':
        try:
            from waitress import serve
        except ImportError:
            raise RuntimeError("waitress not installed; add it to requirements and pip install for production")
        serve(app, host='0.0.0.0', port=port)
    else:
        app.run(host='0.0.0.0', port=port, debug=True)
