# Damareen

Backend az I. forduló (Web-mobil, 2025. nov 7–9) feladatához. Gyűjtögetős fantasy kártyajáték API – Flask, SQLAlchemy, JWT, meg egy kis e-mailes móka. Én is így csinálnám legközelebb, csak kevesebb kávéval.


## Gyors indító (Install + Run)

1) Klónozás és csomagok:

```bash
git clone https://github.com/bbarni2020/Damareen.git
cd Damareen/backend
pip install -r requirements.txt
```

2) Opcionális `.env` (ha nincs, dev defaultok élnek):

```
SECRET_KEY=change-me
DATABASE_URL=sqlite:///app.db
EMAIL_USERNAME=damareen@example.com
EMAIL_PASSWORD=secret
FRONTEND_URL=http://localhost:3000
REQUIRE_EMAIL_VERIFICATION=false
PORT=7621
```

3) Futtatás:

```bash
python run.py
```

Backend: http://localhost:7621

Frontend (egyszerű demó): `web/auth.html` megnyitása böngészőben (vagy VS Code Live Server).


## API alapok

- Alap URL: `/api` (CORS: localhost:3000 és 7621)
- Rate limit: 5 kérés / 10 mp / IP
- Auth: `Authorization: Bearer <jwt>` (24 óráig érvényes)
- E-mail verifikáció: kapcsolható (`REQUIRE_EMAIL_VERIFICATION`), ha be van kapcsolva, loginkor is kérhet megerősítést e-mailben.

Kártyatípusok rövidkódjai (a harci logikához):

- `t` = tűz veri a földet
- `f` = föld veri a vizet
- `v` = víz veri a levegőt
- `l` = levegő veri a tüzet


## Endpontok (főleg ezek miatt vagy itt)

Minden válasz egységesített forma: `{ success: boolean, data?: any, error?: string }`.

### Hitelesítés és fiók

1) POST `/api/user/register` – regisztráció

Body:
```json
{ "username": "janos", "email": "janos@example.com", "password": "Jelszo123" }
```
Szabályok: username 3–80 (betű/szám/underscore), valid e-mail, jelszó min 8 (kis+nagybetű+szám).

2) POST `/api/user/login` – bejelentkezés (username vagy e-mail)

Body:
```json
{ "username": "janos", "password": "Jelszo123" }
```
Ha kell e-mail megerősítés, azt kéri; különben visszaad JWT-t.

3) POST `/api/user/verify-email` – regisztráció megerősítése

Body: `{ "token": "..." }`

4) POST `/api/user/verify-login` – bejelentkezés megerősítése (ha ilyen mód be van kapcsolva)

Body: `{ "token": "..." }`

5) POST `/api/user/resend-verification` – új megerősítő e-mail

Body: `{ "email": "janos@example.com" }`

6) POST `/api/user/password-reset` – jelszó-visszaállítás kérése

Body: `{ "email": "janos@example.com" }`

7) PUT `/api/user/password-reset` – jelszó beállítása tokennel

Body: `{ "token": "...", "password": "UjJelszo123" }`

8) GET `/api/user` – aktuális felhasználó adatai

Header: `Authorization: Bearer <jwt>`

9) DELETE `/api/user/delete` – fiók törlése

Header: `Authorization: Bearer <jwt>`

Body: `{ "password": "Jelszo123" }`


### Világok és tagság

1) POST `/api/create/world` – világ létrehozása (nem kell master jog, de beállíthatod)

Header: `Authorization`

Body:
```json
{ "name": "Középfölde", "user_id": "<sajat-id>", "is_master": true }
```
Vissza: új világ, a saját `world_ids` meződben `is_master` szerint rögzül.

2) POST `/api/game/join` – csatlakozás világba kóddal

Header: `Authorization`

Body: `{ "invite_code": "<world_id>" }`

3) GET `/api/user/list/worlds` – világaid listája (és hogy master vagy-e bennük)

Header: `Authorization`

4) GET `/api/user/is-master?world_id=...` – gyors státusz

Header: `Authorization`

5) DELETE `/api/delete/world` – világ törlése (master kell)

Header: `Authorization`

Body: `{ "world_id": "..." }`


### Kártyák és vezérek

1) POST `/api/create/card` – kártya létrehozása (master kell az adott világhoz)

Header: `Authorization`

Body (lényeges mezők):
```json
{
  "world_id": "...",
  "name": "Aragorn",
  "type": "t|f|v|l",
  "health": 5,
  "damage": 2,
  "picture": "opcionális string"
}
```
Megkötések: `name` max 16 karakter (DB limit), `health` 1–100 (egész), `damage` 2–100 (egész). A `type` csak a fenti rövidkódok egyike. A backend az aktuális user-t teszi tulajdonosnak (`owner_id`).

2) POST `/api/create/leader` – vezér kártya származtatása

Header: `Authorization`

Body:
```json
{ "card_id": "<eredeti-kartya-id>", "damage_doubled": true }
```
Ha `damage_doubled=false`, akkor az életerő duplázódik. A vezér az `is_leader` mezőben az eredeti kártya ID-ját hordozza (igen, stringként – így döntöttünk, működik).

3) POST `/api/create/collection` – játékos gyűjtemény feltöltése másolt lapokkal (master kell)

Header: `Authorization`

Body:
```json
{
  "owner_id": "<jatekos-id>",
  "list_of_cards_ids": ["<vilag-kartya-id>", "..."] ,
  "world_id": "<kotelezo a master ellenorzeshez>"
}
```
Megjegyzés: a middleware a `world_id`-t kéri a master ellenőrzéshez, ezért ide is be kell tenni (maga a handler nem használja, de a jogosultság igen).


### Kazamaták (dungeons)

1) POST `/api/create/dungeon` – kazamata létrehozása (master kell)

Header: `Authorization`

Body:
```json
{ "name": "A mélység királynője", "world_id": "...", "list_of_cards_ids": ["...", "...", "...", "<vezér>"] }
```
Szabályok: a lista hossza csak 1 (egyszerű találkozás), 4 (kis kazamata: 3 sima + 1 vezér) vagy 6 (nagy kazamata: 5 sima + 1 vezér). 4/6 esetén az utolsó lap kötelezően vezér, az előzők nem lehetnek vezérek. A megadott sorrendet pozícióként is beírjuk.

2) GET `/api/world/list/dungeons?world_id=...` – világ kazamatái (master)

3) DELETE `/api/delete/dungeon` – kazamata törlése (master)

Header: `Authorization`

Body: `{ "dungeon_id": "...", "world_id": "..." }`


### Listázások (master jogosultság kell)

- GET `/api/world/list/cards?world_id=...` – a világ összes kártyája
- GET `/api/world/list/users?world_id=...` – a világban lévő felhasználók (és hogy master-e az adott világban)


### Pakli és harc

1) POST `/api/deck` – pakli beállítása

Header: `Authorization`

Body (bármelyik kulcs jó):
```json
{ "cards": ["id1", "id2", "..." ] }
```
Megkötés: pontosan 1, 4 vagy 6 egyedi ID, és mind a saját kártyád legyen. A sorrend -> pozíció.

2) GET `/api/game/dungeon?world_id=...` – kihívható kazamaták (1 vagy 2 darab visszaadása)

3) GET `/api/game/fight?dungeon_id=...` – harc lefolytatása

Vissza: csaták listája (ki nyert és miért: `damage` / `type` / `dungeon_fallback`) és a teljes harc győztese. Nyeremény kiosztás jelenleg nincs automatizálva (lásd lentebb).


### Egyéb

GET `/api/health` – állapotjelzés: `{ "status": "egészséges" }`


## Gyors curl példák

Regisztráció:
```bash
curl -X POST http://localhost:7621/api/user/register \
  -H 'Content-Type: application/json' \
  -d '{"username":"janos","email":"janos@example.com","password":"Jelszo123"}'
```

Világ létrehozása (masterként):
```bash
curl -X POST http://localhost:7621/api/create/world \
  -H 'Authorization: Bearer <JWT>' -H 'Content-Type: application/json' \
  -d '{"name":"Kozeppfolde","user_id":"<sajat-id>","is_master":true}'
```

Kazamata harc:
```bash
curl "http://localhost:7621/api/game/fight?dungeon_id=<id>" \
  -H 'Authorization: Bearer <JWT>'
```


## Ami a versenyhez kell (és ami hiányzik)

Elkészült:
- Világok, világkártyák (sima/vezér), kazamaták (1/4/6 szabályokkal)
- Játékos gyűjtemény (master duplikál a világból a játékosnak)
- Pakli összeállítása és harci szimuláció
- Több világ + több játékos, jogosultság master ellenőrzéssel

Hiányok / ismert korlátok:
- Nyeremény kiosztás győzelem után (pl. +sebzés/+élet) nincs még automatizálva endponton – most kézzel kellene módosítani a kártyát.
- Egyedi névellenőrzés világon belül nincs kikényszerítve (DB csak a hosszt limitálja 16-ra).
- `create_collection` használatához a body-ba be kell tenni `world_id`-t a master ellenőrzés miatt (handler nem használja, middleware igen).
- Képfeltöltés nincs (a `picture` most egyszerű stringként megy a DB-be).
- Előre feltöltött „bemutató játékkörnyezet” nincs automatikusan – kézzel hoztam létre a világot/kazikat.


## Tech stack (röviden)

- Flask 3, Flask-SQLAlchemy (SQLite), Flask-CORS
- bcrypt (jelszavak), PyJWT (token), python-dotenv


## Jegyzetek a fejlesztésből

- A vezér jelölése: az `is_leader` mező nem boolean, hanem az eredeti kártya ID-ja (nem szép, de praktikus a validációhoz). Ha üres string, akkor sima kártya.
- A típusoknál a rövidkódot használom (`t/f/v/l`), a harc emiatt egyszerű és gyors.
- A `position` mezőt használjuk pakli-sorrendként is, harc előtt újraszámozva.
- Rate limitet adtam mindenre (5/10mp). Ha elérted, kapsz 429-et – várj egy pillit.


## Roadmap / To-Do

- Nyeremény kiosztás endpont (kártya fejlődés: +1/+2/+3 megfelelően)
- Előre feltöltött demo világ + kazamaták scriptből
- Képkezelés (fájl / base64), egyszerű galéria
- Szigorúbb név- és típusvalidáció világ szinten
- Frontend UI a pakli szerkesztéséhez (most nagyon basic)


## Biztonság (rövid megjegyzések)

- Bcrypt hash jelszavakra, JWT HS256, CORS csak fejlesztői originre
- Állíts rendes `SECRET_KEY`-et élesben, ne használd a defaultokat
- Token lejár: 24 óra


## Licenc / használat

Nincs formális licenc. Használd nyugodtan, ha valami komolyba menne, dobj egy üzenetet. Ha eltöröd, megtarthatod mindkét darabot.

