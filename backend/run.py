import os
from dotenv import load_dotenv
from app import create_app
from app.models import db
from werkzeug.serving import ThreadedWSGIServer

load_dotenv()  # .env fájlból olvassuk be a környezeti változókat

app = create_app()

# DB inicializálás - ha nem létezik, létrehozza a táblákat
with app.app_context():
    db.init_app(app)
    db.create_all()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 7621))  # 7621 az alapértelmezett port
    env = os.environ.get('FLASK_ENV', 'development')
    if env == 'production':
        # Production módban threaded WSGI szervert használunk
        from werkzeug.serving import ThreadedWSGIServer
        print(f"Starting Damareen server on port {port}")
        server = ThreadedWSGIServer('0.0.0.0', port, app)
        server.serve_forever()
    else:
        # Dev módban Flask beépített szerver debug móddal
        app.run(host='0.0.0.0', port=port, debug=True)
