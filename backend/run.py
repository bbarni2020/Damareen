import os
from dotenv import load_dotenv
from app import create_app
from app.models import db
from werkzeug.serving import ThreadedWSGIServer

load_dotenv()

app = create_app()

with app.app_context():
    db.init_app(app)
    db.create_all()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 7621))
    env = os.environ.get('FLASK_ENV', 'development')
    if env == 'production':
        from werkzeug.serving import ThreadedWSGIServer
        print(f"Starting Damareen server on port {port}")
        server = ThreadedWSGIServer('0.0.0.0', port, app)
        server.serve_forever()
    else:
        app.run(host='0.0.0.0', port=port, debug=True)
