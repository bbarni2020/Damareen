PORT=5000
export PORT

kill -9 $(lsof -ti ":$PORT") 2>/dev/null || true
git pull
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export FLASK_APP=run.py

python3 run.py