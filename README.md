# Damareen

Fantasy kártyajáték, amit a Dusza Árpád Országos Emlékverseny I. fordulójára dobtam össze. Backend Flask + SQLite, elöl van néhány statikus HTML a `web/` mappában. JWT auth, opcionális email verifikáció, rate limiting.

## Mi ez?

Játékmester létrehoz egy világot kártyákkal és dungeonokkal. Játékosok kapnak egy gyűjteményt ebből, összeraknak egy 1/4/6 lapos paklit, aztán dungeonokkal harcolnak. Nyeréskor az egyik általad választott lapod erősebb lesz (+1/+2/+3 stat, típustól függ). Nincs vége a játéknak, csak fejlődnek a lapok.

A projektet gyorsan raktam össze macOS-en Python 3.11-gyel – nem tudom milyen production-ready, de futtatható és működik.

## Gyors start

Kell: Python 3.10+

```bash
git clone https://github.com/bbarni2020/Damareen.git
cd Damareen/backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python run.py
```

Backend indul: http://localhost:7621

Opcionálisan csinálhatsz egy `.env` fájlt a `backend/`-ben (alapból dev mode van):

```env
SECRET_KEY=change-me
DATABASE_URL=sqlite:///app.db
EMAIL_USERNAME=damareen@example.com
EMAIL_PASSWORD=secret
REQUIRE_EMAIL_VERIFICATION=false
PORT=7621
```

Dev módban állítsd `REQUIRE_EMAIL_VERIFICATION=false`-ra, különben SMTP konfigot kell beállítani.

### Docker (alternatíva)

Ha Dockerrel akarod futtatni (Python backend + PHP frontend egy containerben):

```bash
# .env fájl létrehozása (először)
cp .env.example .env
# Szerkeszd a .env-et a saját értékeiddel

# Build & run
docker-compose up -d

# Vagy csak a build
docker build -t damareen .
docker run -p 7621:7621 -p 8000:8000 --env-file .env damareen
```

Backend: http://localhost:7621  
Frontend: http://localhost:8000

**Fontos:** A docker-compose automatikusan beolvassa a project root `.env` fájlt. Másold le a `.env.example`-t `.env`-re és állítsd be a saját értékeidet (SECRET_KEY, email config, stb.).

### Frontend

Van két mód:
1. Nyisd meg közvetlenül a `web/auth.html`-t (gyors teszt)
2. PHP-val futtasd (jobb):

```bash
cd web
php -S 127.0.0.1:8000 index.php
```

Route-ok:
- http://127.0.0.1:8000/ - dashboard
- http://127.0.0.1:8000/auth - login/register
- http://127.0.0.1:8000/manage-world - master funkciók
- http://127.0.0.1:8000/game - harcolás

**Megjegyzés:** A frontend fájlokban jelenleg production URL van (`https://damareen.deakteri.fun/api`). Ha lokálban futtatod, cseréld ki:

| Fájl | Keresendő string | Csere erre |
|------|------------------|------------|
| `auth.html` | `https://damareen.deakteri.fun/api/user` | `http://localhost:7621/user` |
| `dashboard.html` | `https://damareen.deakteri.fun/api` | `http://localhost:7621` |
| `manage_world.html` | `https://damareen.deakteri.fun/api` | `http://localhost:7621` |
| `game.html` | `https://damareen.deakteri.fun/api` | `http://localhost:7621` |

## Architektúra

**Backend stack:**
- Flask 3 + Flask-SQLAlchemy (SQLite)
- Flask-CORS (enged: localhost:3000/5500/7621)
- JWT auth HS256, 24 óra lejárat
- bcrypt jelszó hash
- egyszerű rate limit: 5 req / 10s / IP (in-memory dict, prodban Redis kéne de ez gyors volt)

**Adatmodell:**
- `User` - id, username, email, password_hash, world_ids (JSON dict: {world_id: is_master}), email tokenek
- `World` - world_id, name
- `Card` - id, world_id, owner_id, name (max 16 kar), picture (base64 binary), health, damage, type (t/f/v/l), position, is_leader (ha vezér, eredeti lap id-ja)
- `Dungeon` - id, name, world_id, list_of_card_ids (sorrend számít harcnál)

**Harc logika:**
- Típusok: `t` (tűz) > `f` (föld) > `v` (víz) > `l` (levegő) > `t` (kör)
- Ha match, erősebb típus nyer. Ha nem, összehasonlítja statokat.

**API path-ok:**
- Lokálban: `/user/register`, `/create/world` stb.
- Production (reverse proxy): `/api/user/register`, `/api/create/world` stb.

## API referencia

Auth: `Authorization: Bearer <jwt>` headerben  
Válasz: `{"success": bool, "data"?: any, "error"?: string}`

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

### Világok

```
POST   /create/world            { name, user_id }
POST   /game/join               { world_id }
GET    /user/list/worlds
GET    /user/is-master          ?world_id=...
PUT    /edit/world              { world_id, name } - master only
DELETE /delete/world            { world_id } - master only
```

### Kártyák (master jogosultság kell)

```
POST   /create/card             { world_id, name, type, health, damage, picture? }
POST   /create/leader           { card_id, name, damage_doubled? / health_doubled? }
POST   /create/collection       { owner_id, list_of_cards_ids, world_id }
GET    /world/list/cards        ?world_id=...
POST   /world/user/addcard      { world_id, card_ids, user_ids }
DELETE /world/user/removecard   { world_id, card_ids, user_ids }
DELETE /delete/card             { card_id, world_id }
```

`type` lehet: `t`/`f`/`v`/`l` (tűz/föld/víz/levegő)  
`picture` opcionális base64 string

### Dungeonok (master)

```
POST   /create/dungeon          { name, world_id, list_of_cards_ids }
GET    /world/list/dungeons     ?world_id=...
DELETE /delete/dungeon          { dungeon_id, world_id }
```

Dungeon szabályok:
- 1/4/6 lap lehet összesen
- 4 vagy 6 lapnál az utolsó pozíció vezér kell legyen

### Pakli + Harc (játékos)

```
POST /deck                      { cards: [id1, id2, ...] }
GET  /game/dungeon              ?world_id=...
GET  /game/fight                ?dungeon_id=...&selected_card_id=...
```

Pakli: pontosan 1/4/6 lap kell (sorrend = pozíció).

Harc: `selected_card_id` = melyik saját lapod kapja a jutalom statot ha nyersz:
- 1 lapos dungeon: +1 damage
- 4 lapos: +2 health
- 6 lapos: +3 damage

## curl példák (lokál)

Gyors teszt workflow:

```bash
# Reg
curl -X POST http://localhost:7621/user/register \
  -H 'Content-Type: application/json' \
  -d '{"username":"test","email":"test@test.com","password":"Test1234"}'

# Világ
curl -X POST http://localhost:7621/create/world \
  -H "Authorization: Bearer <JWT>" \
  -H 'Content-Type: application/json' \
  -d '{"name":"Teszt világ","user_id":"<id>"}'

# Kártya
curl -X POST http://localhost:7621/create/card \
  -H "Authorization: Bearer <JWT>" \
  -H 'Content-Type: application/json' \
  -d '{"world_id":"<world>","name":"Gandalf","type":"t","health":10,"damage":5}'

# Vezér
curl -X POST http://localhost:7621/create/leader \
  -H "Authorization: Bearer <JWT>" \
  -H 'Content-Type: application/json' \
  -d '{"card_id":"<lap>","name":"Gandalf a Fehér","damage_doubled":true}'

# Dungeon (4 lap: 3 sima + 1 vezér utoljára)
curl -X POST http://localhost:7621/create/dungeon \
  -H "Authorization: Bearer <JWT>" \
  -H 'Content-Type: application/json' \
  -d '{"name":"Sötét barlang","world_id":"<world>","list_of_cards_ids":["id1","id2","id3","<vezer>"]}'

# Pakli setup
curl -X POST http://localhost:7621/deck \
  -H 'Authorization: Bearer <JWT>' \
  -H 'Content-Type: application/json' \
  -d '{"cards":["id1","id2","id3","id4"]}'

# Harc
curl http://localhost:7621/game/fight?dungeon_id=<dun>&selected_card_id=<lapod> \
  -H 'Authorization: Bearer <JWT>'
```

## Frontend használat

### 1. Regisztráció/Belépés (auth.html)
- Regisztrálsz vagy bejelentkezel
- Dev módban email verifikáció kikapcsolva → egyből JWT-t kapsz
- Ha email verifikáció be van: email linkre kell kattintani

### 2. Dashboard (dashboard.html)
Világok listája két kategóriában:
- **Felfedezés**: minden publikus világ
- **Saját világok**: amikhez csatlakoztál vagy te vagy a master

Kék háttér = te vagy a master

**Start gomb:**
- Master → `manage_world.html`
- Játékos → `game.html`

### 3. Világ management (manage_world.html - master)
Két fő tab:
1. **Kártya készítés**
   - Típus (monster/hero/spell/defense → t/v/f/l belül)
   - Kép feltöltés (optional)
   - Stats: HP, DMG
   - Kiosztás opció: add meg usernek/usereknek azonnal
   
2. **Dungeon készítés**
   - Kattintással jelöld ki a kártyákat sorrendben
   - 1/4/6 lap
   - 4 vagy 6 esetén az utolsó vezér kell legyen

**Vezér készítés:** Kattints egy sima lapra → 👑 gomb jelenik meg → választasz hogy health vagy damage duplázódjon

**Kártya kiosztás/visszavonás:** + és - ikonok a kártyákon

**Világ törlés:** felső piros gomb (minden adat vele megy)

### 4. Játékos nézet (game.html)
- Bal oldalt: pakli kiválasztás (1/4/6 lap)
- Közép: kihívható dungeonok (1-2 db, cache-elve)
- Harc indítás: válaszd ki melyik lapod kapja a jutalom statot

**Frissítés:** bal felső kör gomb (ha új lapokat kaptál)

## Deploy jegyzetek

### Docker deployment

**Gyors indítás (egy container, backend + frontend):**
```bash
docker-compose up -d
```

**Vagy külön containerekben (ajánlott production-re):**
```bash
docker-compose -f docker-compose.separated.yml up -d
```

Ez létrehozza:
- Backend container (Python/Flask) - port 7621
- Frontend container (PHP) - port 8000
- Persistent volume a SQLite DB-hez

**Env var-ok:** Hozz létre egy `.env` fájlt a project root-ban:
```env
SECRET_KEY=your-secret-key-here
REQUIRE_EMAIL_VERIFICATION=false
EMAIL_USERNAME=your-email@example.com
EMAIL_PASSWORD=your-password
```

### Manual deployment

- `run.py` indításkor létrehozza a DB táblákat ha nincsenek
- Production: használj reverse proxy-t (nginx) és tedd elé az `/api` prefix-et
- SMTP config `.env`-ben ha email verifikációt akarsz
- Van egy `setup.sh` script a backend mappában de én kézzel indítom inkább

**Nginx példa config:**
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

## Teszt fiók

Ha csak ki akarod próbálni:

```
Email: test@test.hu
Jelszó: Dusza2025
```

Ez a fiók már létrehozott egy világot ("Dusza"), master jogosultsággal. Bárki csatlakozhat ebbe a játékba.

## Tech details

**Packages:**
- Flask 3.0.0
- Flask-CORS 4.0.0
- Flask-SQLAlchemy 3.1.1
- python-dotenv 1.0.0
- bcrypt 4.1.1
- PyJWT 2.8.0
- waitress 3.0.0 (prod server)

**Biztonsági réteg:**
- bcrypt hash jelszavakhoz
- JWT HS256, 24h lejárat
- CORS csak dev hostokon
- Rate limit alapszinten (5 req/10s/IP)

**DB:**
- SQLite dev-ben
- Production-ben ugyanúgy SQLite mert kis projekt, de át lehet állítani PostgreSQL-re a `DATABASE_URL` env var-ral

---

Ha valami nem működik vagy kérdés van, nyiss issue-t. A kód nem tökéletes de működik.
