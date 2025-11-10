# Damareen

Gyűjtögetős fantasy kártyajáték (I. forduló Dusza Árpád Országos Emlékverseny). Backend Flask + SQLite, egy minimalista statikus „frontend” a `web/` mappában. E-mail verifikáció, JWT, rate limit.
## Miről szól? (rövid pitch)

Játékmester világot hoz létre (világkártyák + kazamaták), ebből a játékos kap saját gyűjteményt, összeállít paklit (1/4/6 lap), majd kazamatákkal harcol. Nyersz? Az egyik kiválasztott saját lapod automatikusan fejlődik (típusfüggő +1/+2/+3). A játék nem ér véget – fejleszthetsz tovább.


## Gyors indító

Előfeltétel: Python 3.10+ (nálam 3.11-gyel futott), macOS-en a következőt használtam.

1) Klónozás és csomagok

```bash
git clone https://github.com/bbarni2020/Damareen.git
cd Damareen/backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

2) Opcionális `.env` (ha nincs, dev defaultok élnek)

```
SECRET_KEY=change-me
DATABASE_URL=sqlite:///app.db
EMAIL_USERNAME=damareen@example.com
EMAIL_PASSWORD=secret
FRONTEND_URL=http://localhost:3000
REQUIRE_EMAIL_VERIFICATION=false
PORT=7621
```

Tipp: fejlesztéshez kapcsold ki az e-mail verifikációt (`REQUIRE_EMAIL_VERIFICATION=false`), különben SMTP-t kell belőnöd.

3) Futtatás

```bash
python run.py
```

Backend: http://localhost:7621

Frontend: két módon is használható:

- Közvetlen HTML megnyitással (gyors prototípus): nyisd meg a `web/auth.html`-t.
- Szerveresen, PHP-val – ajánlott: a `web/index.php` egy pici router és ez a fő belépési pont. URL-ek: `/` (dashboard), `/auth`, `/manage-world`, `/game`.

Gyors indítás PHP-val:

```bash
cd web
php -S 127.0.0.1:8000 index.php
```

Ezután nyisd meg:

- http://127.0.0.1:8000/          (dashboard)
- http://127.0.0.1:8000/auth      (bejelentkezés)
- http://127.0.0.1:8000/manage-world  (világ menedzsment)
- http://127.0.0.1:8000/game      (játék)


## Architektúra dióhéjban

- Backend: Flask 3, Flask-SQLAlchemy (SQLite), Flask-CORS, PyJWT, bcrypt, python-dotenv
- Adatmodell:
  - User: id, username, email, password_hash, world_ids (dict: world_id -> is_master), email tokenek
  - World: world_id, name
  - Card: id, world_id, owner_id, name (max 16), picture (base64 binary), health, damage, type (t/f/v/l), position (pakli), is_leader (eredeti sima kártya id-ja vagy "")
  - Dungeon: id, name, world_id, list_of_card_ids (sorrend számít)
- CORS: localhost:3000/5500/7621 engedélyezett
- Rate limit: 5 kérés / 10 mp / IP
- Token: saját HS256 JWT 24 órás lejárattal


## API használat – alapok

- Auth header: `Authorization: Bearer <jwt>`
- Válaszok: `{ success: boolean, data?: any, error?: string }`
- Típusok rövidkódjai a harcban: `t` (tűz) veri `f` (föld) veri `v` (víz) veri `l` (levegő) veri `t`

Fontos a path-okhoz:

- Lokálisan az útvonalak a gyökéren vannak (pl. `/user/register`).
- Deploy alatt reverse proxy mögött `/api` prefixszel mennek (pl. `/api/user/register`).

Az alábbi példákban a „/api/…” alakot használom. Ha lokálban futtatod, cseréld `http://localhost:7621/api/...` helyett `http://localhost:7621/...`-ra.


## Endpontok (összefoglaló)

Hitelesítés / fiók

1) POST `/api/user/register` – regisztráció

Body: `{ "username": "janos", "email": "janos@example.com", "password": "Jelszo123" }`

2) POST `/api/user/login` – bejelentkezés (username vagy e-mail)

Body: `{ "username": "janos", "password": "Jelszo123" }`

3) POST `/api/user/verify-email` – regisztráció megerősítése (token)

4) POST `/api/user/resend-verification` – megerősítő e-mail újraküldése

5) POST `/api/user/password-reset` – jelszó-visszaállítás kérése (e-mail)

6) PUT `/api/user/password-reset` – jelszó beállítása tokennel

7) GET `/api/user` – aktuális user (név, e-mail, settings)

8) DELETE `/api/user/delete` – fiók törlése (jelszó kell)


Világok és tagság

1) POST `/api/create/world` – világ létrehozása (a hívó lesz master)

Body: `{ "name": "Kozeppfolde", "user_id": "<sajat-id>" }`

2) POST `/api/game/join` – csatlakozás világba kóddal (a kód maga a `world_id`)

3) GET `/api/user/list/worlds` – világaid (és melyikben vagy master)

4) GET `/api/user/is-master?world_id=...` – gyors státusz

5) PUT `/api/edit/world` – világ átnevezése (master)

6) DELETE `/api/delete/world` – világ törlése (master)


Kártyák és vezérek (master)

1) POST `/api/create/card` – sima kártya létrehozása

Body: `{ "world_id": "...", "name": "Aragorn", "type": "t|f|v|l", "health": 5, "damage": 2 }`

2) POST `/api/create/leader` – vezérkártya származtatása simából

Body: `{ "card_id": "<sima-id>", "name": "Darth ObiWan", "damage_doubled": true }`

3) POST `/api/create/collection` – játékos gyűjtemény feltöltése másolatokkal

Body: `{ "owner_id": "<jatekos-id>", "list_of_cards_ids": ["id1","id2"], "world_id": "..." }`

4) GET `/api/world/list/cards?world_id=...` – világ (saját) kártyáid

5) POST `/api/world/user/addcard` – kártya másolat adása felhasználónak/felhasználóknak

6) DELETE `/api/world/user/removecard` – kártya(ák) elvétele felhasználótól/felhasználóktól

7) DELETE `/api/delete/card` – kártyanév teljes törlése világból (minden példány + vezérek, és dungeonec tisztítás)


Kazamaták (master)

1) POST `/api/create/dungeon` – kazamata létrehozása (1 | 4 | 6 kártya; 4/6-nál az utolsó vezér)

2) GET `/api/world/list/dungeons?world_id=...` – világ kazamatái

3) DELETE `/api/delete/dungeon` – kazamata törlése


Pakli és harc (játékos)

1) POST `/api/deck` – pakli beállítása: pontosan 1, 4 vagy 6 saját kártya azonosítója, sorrend = pozíció

Body: `{ "cards": ["id1", "id2", ...] }`

2) GET `/api/game/dungeon?world_id=...` – 1-2 kihívható kazamata (cache-elve user+világ szerint)

3) GET `/api/game/fight?dungeon_id=...&selected_card_id=...` – harc; ha nyersz, a kiválasztott saját lapod fejlődik:

- 1 lapos dungeon: +1 sebzés
- 4 lapos dungeon: +2 életerő
- 6 lapos dungeon: +3 sebzés


Egyéb

- GET `/api/health` – egészségügyi állapot


## Gyors curl – egy kerek kör

Regisztráció (dev módban azonnal tokennel tér vissza):

```bash
curl -sS -X POST http://localhost:7621/user/register \
  -H 'Content-Type: application/json' \
  -d '{"username":"janos","email":"janos@example.com","password":"Jelszo123"}'
```

Világ létrehozása (a tokeneddel):

```bash
curl -sS -X POST http://localhost:7621/create/world \
  -H "Authorization: Bearer <JWT>" -H 'Content-Type: application/json' \
  -d '{"name":"Kozeppfolde","user_id":"<sajat-id>"}'
```

Kártyák + vezér, majd dungeon (példa):

```bash
# sima lap
curl -sS -X POST http://localhost:7621/create/card \
  -H "Authorization: Bearer <JWT>" -H 'Content-Type: application/json' \
  -d '{"world_id":"<world>","name":"Aragorn","type":"t","health":5,"damage":2}'

# vezér a fenti simából
curl -sS -X POST http://localhost:7621/create/leader \
  -H "Authorization: Bearer <JWT>" -H 'Content-Type: application/json' \
  -d '{"card_id":"<aragorn-id>","name":"Király Aragorn","damage_doubled":true}'

# kis kazamata: 3 sima + 1 vezér (utolsó vezér legyen)
curl -sS -X POST http://localhost:7621/create/dungeon \
  -H "Authorization: Bearer <JWT>" -H 'Content-Type: application/json' \
  -d '{"name":"A mélység királynője","world_id":"<world>","list_of_cards_ids":["id1","id2","id3","<vezér-id>"]}'
```

Pakli és harc:

```bash
# pakli (pont 4 lap) – a saját példányaid azonosítóival
curl -sS -X POST 'http://localhost:7621/deck' \
  -H 'Authorization: Bearer <JWT>' -H 'Content-Type: application/json' \
  -d '{"cards":["idA","idB","idC","idD"]}'

# harc (meg kell adni a kiválasztott saját kártyád id-ját is a jutalomhoz)
curl -sS 'http://localhost:7621/game/fight?dungeon_id=<dun>&selected_card_id=<sajat-kartya-id>' \
  -H 'Authorization: Bearer <JWT>'
```

Megjegyzés: a fenti példák a lokális (prefix nélküli) útvonalat használják. Ha reverse proxy mögött fut, told elé az `/api`-t.



## Frontend jegyzetek

- A `web/` mappa statikus: `auth.html`, `dashboard.html`, `manage_world.html`, `game.html` – és egy `index.php`, ami a fő belépési pontként routerel ezekre az oldalakra.
- Az `auth.html` jelenleg egy távoli API URL-re mutat: `https://damareen.deakteri.fun/api/...` – ha lokál backenddel dolgozol, cseréld a fájlban az `API_URL`-t `http://localhost:7621/user`-re (és a többi nézetben `http://localhost:7621`-re)
- Képek/ikonok: `web/src/`

## Frontend használati útmutató (lépésről lépésre)



### 1. Belépés / Regisztráció (`auth.html`)
1. Ha PHP-t használsz: nyisd meg a http://127.0.0.1:8000/auth oldalt (lásd fent). Alternatívaként megnyithatod közvetlenül a `web/auth.html`-t is (dev próba).
2. Regisztráció: beírod a nevet / e-mailt / jelszót. Ha email verifikáció ki van kapcsolva (`REQUIRE_EMAIL_VERIFICATION=false`), azonnal kapsz JWT-t és átugrik a dashboardra.
3. Ha be van kapcsolva: kapsz egy üzenetet, és várnod kell a linkre. Dev módban én ezt általában kikapcsolom.
4. Elfelejtett jelszó és reset ugyanitt – token paraméterrel új form jelenik meg.

API_URL csere lokálhoz: a fájl tetején van `const API_URL = 'https://damareen.deakteri.fun/api/user';` – írd át: `const API_URL = 'http://localhost:7621/user';`

### 2. Világ választás (`dashboard.html`)
Belépés után automatikus átirányítás ide. Két sor: „Felfedezés” (világok listája) és „Saját világok” (ahova már csatlakoztál vagy master vagy). Kattintás kiemeli (outline). Master világ kártyája kékes háttérrel jön.

Gombok bal felül:
- Plusz (világ hozzáadása) – ha nincs world_id paraméter később, a `manage_world.html` üres módban indul.
- Frissítés – újra lehúzza a világlistát (ha közben valaki mást létrehozott). Néha itt kellén frissíteni, mert nincs auto-poll.

Start gomb:
- Ha master vagy a kiválasztott világban → `manage_world.html?world_id=...`
- Ha sima játékos → `game.html?world_id=...`

Lokál API_URL csere: itt `const API_URL = 'https://damareen.deakteri.fun/api';` → legyen `http://localhost:7621`.

### 3. Világ menedzsment (Master nézet – `manage_world.html`)
Két fő tab: Kártyakészítés + Kazamata készítés. Addig zár (szürkít) minden, amíg nincs világ létrehozva.

Lépések friss világ esetén:
1. Írd be a világ nevét a nagy címbe (placeholder „Kezdj gépelni”).
2. „Világ létrehozása” gomb – siker után UI feloldódik.
3. Kártyák: válassz típust (a belső mapping: monster→t, hero→v, spell→f, defense→l). Adj képet (opcionális), nevet, HP, DMG.
4. (Opcionális) kiosztás létrehozáskor: a „Kiosztás nélkül” select alatt beállíthatod, hogy a kártya azonnal menjen egy usernek / több usernek / mindenkinek. Ha több játékos már csatlakozott, akkor listázza őket.
5. Mentés → megjelenik jobb oldalt a „Gyűjtemény”-ben.
6. Leader létrehozás: kattints egy sima kártyára → megjelenik kis „👑” gomb (ha még nincs belőle vezér). Ott eldöntöd melyik stat duplázódjon (health vagy damage). Az eredeti kártyához kapcsolódik (`is_leader`), dungeonben az utolsó pozíció vezér kell legyen.
7. Kazamata: válts át a tabra → a „Kazamata sorrend” blokkban kattintással jelöld ki a lejátszási sorrendet (1 / 4 / 6 kártya – 4/6-nál az utolsó vezér). Gombbal névadás + létrehozás.
8. Kazamata törlés: a listában piros X.
9. Kártya kiosztása / visszavonása utólag: kártyán a zöld „+” (give) és narancs „−” (remove) ikon – modálban választasz usert / user(eke)t.
10. Világ törlése: felső piros gomb – minden kártya, vezér, dungeon megy vele.

Mobilon: sok UI elem összecsukott, a világ létrehozás után kap egy `world-active` állapotot – ha zavar, fejlesztés közben nyisd desktop nézetben.

Lokál API_URL: `const API_URL = 'https://damareen.deakteri.fun/api';` → `http://localhost:7621`

Frissítés szükségessége (itt különösen):
- Új kártya / vezér létrehozása után néha nem jelenik meg azonnal a dungeon tabban – kattints át oda vagy manuálisan reload (CMD+R).
- Kiosztás / visszavonás után a játékos oldalon (game.html) a saját gyűjtemény csak új lekéréskor frissül.

### 4. Játékos nézet (harc) – `game.html`
Ha nem vagy master, a „Start” erre visz. Felépítés:
- Bal oldalt a saját paklid jelölhető (deck beállítása endpointon keresztül – a JS intézi).
- Középen listázódnak kihívható kazamaták (általában 1-2, cache-elve).
- Kiválasztasz egyet → harc endpont: megadod melyik saját kártyát jelöld jutalomra (`selected_card_id`).
- Nyerés esetén automatikus stat növelés: 1 lapos dungeon +1 DMG, 4 lapos +2 HP, 6 lapos +3 DMG.
- Jutalom után azonnal frissíteni akarod? Reload – mivel a lap állapota lokál memóriában még régi lehet.

UI gombok:
- Bal felső kör frissítés – újra lehúzza a listákat.
- Jobb felső home – vissza a dashboardra.

Lokál API_URL: itt is `https://damareen.deakteri.fun/api` → `http://localhost:7621`

### 5. API_URL gyors csere összefoglaló
| Fájl | Eredeti | Lokálra írd át |
| ---- | ------- | -------------- |
| `auth.html` | `https://damareen.deakteri.fun/api/user` | `http://localhost:7621/user` |
| `dashboard.html` | `https://damareen.deakteri.fun/api` | `http://localhost:7621` |
| `manage_world.html` | `https://damareen.deakteri.fun/api` | `http://localhost:7621` |
| `game.html` | `https://damareen.deakteri.fun/api` | `http://localhost:7621` |


### 6. Hibakeresési mini forgatókönyv
„Létrehoztam egy kártyát, de nem látom a dungeon tabon”:
1. Kártya valóban sikerült? (Network → 200 + JSON success)
2. Van világ_id a query-ben? (`?world_id=...` – ha nem, rossz módba kerültél)
3. Dungeon tabra átkattintás? (render újrahívja)
4. Ha továbbra sem: reload → ha még mindig semmi, név-ütközés volt és a kártya nem jött létre.

„Jutalom nem látszik harc után”: reload `game.html`; deck új lekérése.

„Nem tudok világot törölni”: Valószínű nincs master jogosultság (ellenőrizd a dashboardon kék háttérrel jelölt világot).


## Telepítés/üzemeltetés jegyzetek

- A `backend/run.py` indításkor létrehozza a táblákat (SQLite)
- Prod környezetben reverse proxy-val ajánlott `/api` prefixet adni a backend elé
- SMTP: `.env`-ben add meg az `EMAIL_USERNAME`/`EMAIL_PASSWORD` párost; dev-ben kapcsold ki a verifikációt
- Van egy kényelmi script (`backend/setup.sh`), ami virtualenvet készít és indít – nálam inkább kézzel fut.


## Védelmi és minőségbeli apróságok

- Jelszavak bcrypt-tel hash-elve
- JWT HS256, 24 órás lejárat
- CORS csak fejlesztői hostokra
- Egységes JSON válaszok, hibák 4xx/5xx kódokkal


## Teszt fiók (előre létrehozott világ)

Ha csak kipróbálnád a felületet és az API-t egyből kész világgal:

- E-mail: `test@test.hu`
- Jelszó: `Dusza2025`

Ezzel a fiókkal már van egy létrehozott világ (ő a játékmester), így azonnal lehet csatlakozni/játszani, vagy masterként kártyákat és kazamatákat kezelni.

A world neve: Dusza. Bármely más fiókról szabadon lehet csatlakozni ebbe a játékba.
