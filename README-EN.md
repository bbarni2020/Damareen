# Damareen

Fantasy card game I threw together for the 1st round of the Dusza Árpád National Memorial Competition. Backend is Flask + SQLite, frontend has some static HTML files in the `web/` folder. JWT auth, optional email verification, rate limiting.

## What's this?

A game master creates a world with cards and dungeons. Players get a collection from these, build a 1/4/6 card deck, then fight dungeons. When you win, one card you choose gets stronger (+1/+2/+3 stat, depends on type). There's no endgame, cards just keep evolving.

Put this project together quickly on macOS with Python 3.11 – not sure how production-ready it is, but it runs and works.

## Quick start

Need: Python 3.10+

```bash
git clone https://github.com/bbarni2020/Damareen.git
cd Damareen/backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python run.py
```

Backend starts at: http://localhost:7621

Optionally create a `.env` file in `backend/` (defaults to dev mode):

```env
SECRET_KEY=change-me
DATABASE_URL=sqlite:///app.db
EMAIL_USERNAME=damareen@example.com
EMAIL_PASSWORD=secret
REQUIRE_EMAIL_VERIFICATION=false
PORT=7621
```

In dev mode set `REQUIRE_EMAIL_VERIFICATION=false`, otherwise you need to configure SMTP.

### Docker (alternative)

If you want to run with Docker (Python backend + PHP frontend in one container):

```bash
# Create .env file (first time)
cp .env.example .env
# Edit .env with your own values

# Build & run
docker-compose up -d

# Or just build
docker build -t damareen .
docker run -p 7621:7621 -p 8000:8000 --env-file .env damareen
```

Backend: http://localhost:7621  
Frontend: http://localhost:8000

**Important:** docker-compose automatically reads the `.env` file from project root. Copy `.env.example` to `.env` and set your own values (SECRET_KEY, email config, etc.).

### Frontend

Two ways to run:
1. Open `web/auth.html` directly (quick test)
2. Run with PHP (better):

```bash
cd web
php -S 127.0.0.1:8000 index.php
```

Routes:
- http://127.0.0.1:8000/ - dashboard
- http://127.0.0.1:8000/auth - login/register
- http://127.0.0.1:8000/manage-world - master functions
- http://127.0.0.1:8000/game - combat

**Note:** Frontend files currently have production URL (`https://damareen.deakteri.fun/api`). If running locally, replace:

| File | Search for | Replace with |
|------|------------|--------------|
| `auth.html` | `https://damareen.deakteri.fun/api/user` | `http://localhost:7621/user` |
| `dashboard.html` | `https://damareen.deakteri.fun/api` | `http://localhost:7621` |
| `manage_world.html` | `https://damareen.deakteri.fun/api` | `http://localhost:7621` |
| `game.html` | `https://damareen.deakteri.fun/api` | `http://localhost:7621` |

## Architecture

**Backend stack:**
- Flask 3 + Flask-SQLAlchemy (SQLite)
- Flask-CORS (allows: localhost:3000/5500/7621)
- JWT auth HS256, 24 hour expiration
- bcrypt password hash
- simple rate limit: 5 req / 10s / IP (in-memory dict, should be Redis for prod but this was quick)

**Data model:**
- `User` - id, username, email, password_hash, world_ids (JSON dict: {world_id: is_master}), email tokens
- `World` - world_id, name
- `Card` - id, world_id, owner_id, name (max 16 chars), picture (base64 binary), health, damage, type (t/f/v/l), position, is_leader (if leader, original card id)
- `Dungeon` - id, name, world_id, list_of_card_ids (order matters in combat)

**Combat logic:**
- Types: `t` (fire) > `f` (earth) > `v` (water) > `l` (air) > `t` (circle)
- If match, stronger type wins. If not, compares stats.

**API paths:**
- Locally: `/user/register`, `/create/world` etc.
- Production (reverse proxy): `/api/user/register`, `/api/create/world` etc.

## API reference

Auth: `Authorization: Bearer <jwt>` in header  
Response: `{"success": bool, "data"?: any, "error"?: string}`

### Auth / User

```
POST   /user/register           { username, email, password }
POST   /user/login              { username, password }
POST   /user/verify-email       { token }
POST   /user/resend-verification
POST   /user/password-reset     { email }
PUT    /user/password-reset     { token, new_password }
GET    /user
DELETE /user/delete             { password }
```

### Worlds

```
POST   /create/world            { name, user_id }
POST   /game/join               { world_id }
GET    /user/list/worlds
GET    /user/is-master          ?world_id=...
PUT    /edit/world              { world_id, name } - master only
DELETE /delete/world            { world_id } - master only
```

### Cards (master permission required)

```
POST   /create/card             { world_id, name, type, health, damage, picture? }
POST   /create/leader           { card_id, name, damage_doubled? / health_doubled? }
POST   /create/collection       { owner_id, list_of_cards_ids, world_id }
GET    /world/list/cards        ?world_id=...
POST   /world/user/addcard      { world_id, card_ids, user_ids }
DELETE /world/user/removecard   { world_id, card_ids, user_ids }
DELETE /delete/card             { card_id, world_id }
```

`type` can be: `t`/`f`/`v`/`l` (fire/earth/water/air)  
`picture` optional base64 string

### Dungeons (master)

```
POST   /create/dungeon          { name, world_id, list_of_cards_ids }
GET    /world/list/dungeons     ?world_id=...
DELETE /delete/dungeon          { dungeon_id, world_id }
```

Dungeon rules:
- Can have 1/4/6 cards total
- For 4 or 6 cards, last position must be a leader

### Deck + Combat (player)

```
POST /deck                      { cards: [id1, id2, ...] }
GET  /game/dungeon              ?world_id=...
GET  /game/fight                ?dungeon_id=...&selected_card_id=...
```

Deck: needs exactly 1/4/6 cards (order = position).

Combat: `selected_card_id` = which of your cards gets the reward stat if you win:
- 1 card dungeon: +1 damage
- 4 cards: +2 health
- 6 cards: +3 damage

## curl examples (local)

Quick test workflow:

```bash
# Register
curl -X POST http://localhost:7621/user/register \
  -H 'Content-Type: application/json' \
  -d '{"username":"test","email":"test@test.com","password":"Test1234"}'

# World
curl -X POST http://localhost:7621/create/world \
  -H "Authorization: Bearer <JWT>" \
  -H 'Content-Type: application/json' \
  -d '{"name":"Test world","user_id":"<id>"}'

# Card
curl -X POST http://localhost:7621/create/card \
  -H "Authorization: Bearer <JWT>" \
  -H 'Content-Type: application/json' \
  -d '{"world_id":"<world>","name":"Gandalf","type":"t","health":10,"damage":5}'

# Leader
curl -X POST http://localhost:7621/create/leader \
  -H "Authorization: Bearer <JWT>" \
  -H 'Content-Type: application/json' \
  -d '{"card_id":"<card>","name":"Gandalf the White","damage_doubled":true}'

# Dungeon (4 cards: 3 normal + 1 leader last)
curl -X POST http://localhost:7621/create/dungeon \
  -H "Authorization: Bearer <JWT>" \
  -H 'Content-Type: application/json' \
  -d '{"name":"Dark cave","world_id":"<world>","list_of_cards_ids":["id1","id2","id3","<leader>"]}'

# Deck setup
curl -X POST http://localhost:7621/deck \
  -H 'Authorization: Bearer <JWT>' \
  -H 'Content-Type: application/json' \
  -d '{"cards":["id1","id2","id3","id4"]}'

# Combat
curl http://localhost:7621/game/fight?dungeon_id=<dun>&selected_card_id=<yourcard> \
  -H 'Authorization: Bearer <JWT>'
```

## Frontend usage

### 1. Register/Login (auth.html)
- Register or log in
- In dev mode email verification is off → you get JWT immediately
- If email verification is on: need to click email link

### 2. Dashboard (dashboard.html)
List of worlds in two categories:
- **Discover**: all public worlds
- **My worlds**: ones you joined or you're the master

Blue background = you're the master

**Start button:**
- Master → `manage_world.html`
- Player → `game.html`

### 3. World management (manage_world.html - master)
Two main tabs:
1. **Card creation**
   - Type (monster/hero/spell/defense → t/v/f/l internally)
   - Image upload (optional)
   - Stats: HP, DMG
   - Distribution option: assign to user/users immediately
   
2. **Dungeon creation**
   - Click to select cards in order
   - 1/4/6 cards
   - For 4 or 6, last one must be a leader

**Leader creation:** Click a regular card → 👑 button appears → choose whether health or damage doubles

**Card distribution/removal:** + and - icons on cards

**Delete world:** top red button (all data goes with it)

### 4. Player view (game.html)
- Left side: deck selection (1/4/6 cards)
- Center: challengeable dungeons (1-2, cached)
- Start combat: select which card gets the reward stat

**Refresh:** top left circle button (if you got new cards)

## Deploy notes

### Docker deployment

**Quick start (one container, backend + frontend):**
```bash
docker-compose up -d
```

**Or in separate containers (recommended for production):**
```bash
docker-compose -f docker-compose.separated.yml up -d
```

This creates:
- Backend container (Python/Flask) - port 7621
- Frontend container (PHP) - port 8000
- Persistent volume for SQLite DB

**Env vars:** Create a `.env` file in project root:
```env
SECRET_KEY=your-secret-key-here
REQUIRE_EMAIL_VERIFICATION=false
EMAIL_USERNAME=your-email@example.com
EMAIL_PASSWORD=your-password
```

### Manual deployment

- `run.py` creates DB tables on startup if they don't exist
- Production: use a reverse proxy (nginx) and add the `/api` prefix
- SMTP config in `.env` if you want email verification
- There's a `setup.sh` script in the backend folder but I start it manually

**Nginx example config:**
```nginx
location /api/ {
    proxy_pass http://localhost:7621/;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
}

location / {
    proxy_pass http://localhost:8000/;
}
```

## Test account

If you just want to try it out:

```
Email: test@test.hu
Password: Dusza2025
```

This account already created a world ("Dusza") with master permissions. Anyone can join this game.

## Tech details

**Packages:**
- Flask 3.0.0
- Flask-CORS 4.0.0
- Flask-SQLAlchemy 3.1.1
- python-dotenv 1.0.0
- bcrypt 4.1.1
- PyJWT 2.8.0
- waitress 3.0.0 (prod server)

**Security layer:**
- bcrypt hash for passwords
- JWT HS256, 24h expiration
- CORS only on dev hosts
- Basic rate limit (5 req/10s/IP)

**DB:**
- SQLite in dev
- Production also SQLite because small project, but can switch to PostgreSQL with the `DATABASE_URL` env var

---

If something doesn't work or you have questions, open an issue. Code isn't perfect but it works.
