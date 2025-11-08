# Damareen

Egy kártyajáték backend API és webes frontend – Flask-kel, SQLAlchemy-vel meg egy kis e-mail verifikációval. Azért csináltam, mert kellett valami projekthez meg jó móka volt összedobni.


## Tech stack

**Backend:**
- Flask 3.0.0
- Flask-SQLAlchemy (SQLite adatbázissal)
- Flask-CORS (hogy a frontend tudjon beszélni vele)
- bcrypt (jelszó hash-eléshez)
- PyJWT (token-ös auth)
- python-dotenv (környezeti változókhoz)

**Frontend:**
- Vanilla JS + HTML/CSS (semmi fancy framework)
- Google Fonts (Jaro, Fira Code)

## Telepítés

Klónozd le a repót:
```bash
git clone https://github.com/bbarni2020/Damareen.git
cd Damareen
```

Telepítsd a Python csomagokat:
```bash
cd backend
pip install -r requirements.txt
```

Környezeti változók (opcionális, `.env` fájlban):
```
SECRET_KEY=valami-titkos-kulcs
JWT_SECRET_KEY=masik-titkos-kulcs
DATABASE_URL=sqlite:///app.db
EMAIL_USERNAME=damareen@deakteri.fun
EMAIL_PASSWORD=titkos-jelszo
FRONTEND_URL=http://localhost:3000
REQUIRE_EMAIL_VERIFICATION=false
PORT=7621
```

Ha nincs `.env`, akkor dev-secret-key-ekkel fog menni minden.

## Futtatás

Backend indítása:
```bash
cd backend
python run.py
```

Alapból a `http://localhost:7621` címen fog futni.

A frontend megnyitásához csak nyisd meg a `web/auth.html` fájlt egy böngészőben, vagy használj egy local servert (pl. Live Server VSCode-ban).

## API Endpointok

Minden endpoint a `/api` prefix-szel kezdődik. Rate limiting be van kapcsolva: **5 kérés / 10 másodperc** IP-nként.

### Hitelesítés

#### `POST /api/register`
Új felhasználó regisztrálása.

**Request Body:**
```json
{
  "username": "janos",
  "email": "janos@example.com",
  "password": "Jelszo123"
}
```

**Validációs szabályok:**
- Felhasználónév: 3–80 karakter, csak betű, szám, aláhúzás
- E-mail: valid e-mail formátum
- Jelszó: min. 8 karakter, kis- és nagybetű, szám kell

**Response (201):**
```json
{
  "success": true,
  "data": {
    "message": "Regisztráció sikeres. Kérjük, ellenőrizd az e-mail fiókodat a megerősítéshez.",
    "user": {
      "id": "abc123...",
      "username": "janos",
      "email": "janos@example.com",
      "email_verified": false
    },
    "requires_verification": true
  }
}
```

Ha az `REQUIRE_EMAIL_VERIFICATION=false`, akkor azonnal visszaad egy token-t is.

---

#### `POST /api/login`
Bejelentkezés felhasználónévvel vagy e-mail-lel.

**Request Body:**
```json
{
  "username": "janos",
  "password": "Jelszo123"
}
```

**Response (200):**
```json
{
  "success": true,
  "data": {
    "message": "Bejelentkezési megerősítő e-mailt küldtünk.",
    "requires_verification": true
  }
}
```

Ha nincs e-mail verifikáció, akkor egy JWT token-t kapsz vissza, amit az `Authorization: Bearer <token>` headerben tudsz használni.

---

#### `POST /api/verify-email`
E-mail cím megerősítése regisztráció után.

**Request Body:**
```json
{
  "token": "verification-token-from-email"
}
```

**Response (200):**
```json
{
  "success": true,
  "data": {
    "message": "E-mail cím sikeresen megerősítve",
    "user": { ... },
    "token": "jwt-token"
  }
}
```

---

#### `POST /api/verify-login`
Bejelentkezési token megerősítése (ha be van kapcsolva az e-mail-es bejelentkezési verifikáció).

**Request Body:**
```json
{
  "token": "login-verification-token"
}
```

**Response (200):**
```json
{
  "success": true,
  "data": {
    "message": "Bejelentkezés sikeresen megerősítve",
    "user": { ... },
    "token": "jwt-token"
  }
}
```

---

#### `POST /api/resend-verification`
Új megerősítő e-mail küldése, ha lejárt az előző.

**Request Body:**
```json
{
  "email": "janos@example.com"
}
```

**Response (200):**
```json
{
  "success": true,
  "data": {
    "message": "Új megerősítő e-mailt küldtünk"
  }
}
```

---

#### `DELETE /api/account`
Felhasználói fiók törlése (autentikált végpont).

**Headers:**
```
Authorization: Bearer <jwt-token>
```

**Request Body:**
```json
{
  "password": "Jelszo123"
}
```

**Response (200):**
```json
{
  "success": true,
  "data": {
    "message": "A fiók sikeresen törölve"
  }
}
```

---

### Játékelemek

#### `POST /api/create/world`
Új világ létrehozása (autentikált végpont).

**Headers:**
```
Authorization: Bearer <jwt-token>
```

**Request Body:**
```json
{
  "name": "Középfölde"
}
```

**Response (201):**
```json
{
  "success": true,
  "data": {
    "message": "Világ sikeresen létrehozva",
    "world": {
      "world_id": "abc123...",
      "name": "Középfölde"
    }
  }
}
```

---

#### `POST /api/create/card`
Új kártya létrehozása (autentikált végpont).

**Headers:**
```
Authorization: Bearer <jwt-token>
```

**Request Body:**
```json
{
  "world_id": "abc123",
  "user_id": "user456",
  "name": "Sárkány",
  "type": "enemy",
  "health": 100,
  "damage": 25,
  "position": 1,
  "is_leader": false,
  "picture": "base64_encoded_string_or_null"
}
```

**Mezők:**
- `world_id` (string): Világ azonosítója
- `user_id` (string): Tulajdonos azonosítója
- `name` (string, max 16 karakter): Kártya neve
- `type` (string, max 6 karakter): Kártyatípus (pl. "enemy", "hero", stb.)
- `health` (int): Életerő
- `damage` (int): Sebzés
- `position` (int): Pozíció a játéktéren
- `is_leader` (bool): Vezér-e
- `picture` (string/null): Kép base64 kódolással vagy null

**Response (201):**
```json
{
  "success": true,
  "data": {
    "message": "Kártya sikeresen létrehozva",
    "card": {
      "id": "card789",
      "world_id": "abc123",
      "owner_id": "user456",
      "name": "Sárkány",
      "picture": null,
      "health": 100,
      "damage": 25,
      "type": "enemy",
      "position": 1,
      "is_leader": false
    }
  }
}
```

---

#### `POST /api/create/dungeon`
Új dungeon létrehozása (autentikált végpont).

**Headers:**
```
Authorization: Bearer <jwt-token>
```

**Request Body:**
```json
{
  "name": "Sötét barlang",
  "world_id": "abc123",
  "list_of_cards_ids": ["card789", "card012"]
}
```

**Response (201):**
```json
{
  "success": true,
  "data": {
    "message": "Dungeon sikeresen létrehozva",
    "dungeon": {
      "id": "dungeon345",
      "name": "Sötét barlang",
      "world_id": "abc123",
      "list_of_card_ids": ["card789", "card012"]
    }
  }
}
```

---

### Egyéb

#### `GET /api/health`
Szerver állapot ellenőrzése.

**Response (200):**
```json
{
  "success": true,
  "data": {
    "status": "egészséges"
  }
}
```

---

## Adatbázis modellek

### User
```python
id: String (32 karakter, UUID hex)
username: String (80, unique)
email: String (120, unique)
password_hash: String (256)
world_ids: JSON lista
settings: JSON objektum
email_verified: Boolean
verification_token: String (256)
verification_token_expires: DateTime
login_verification_token: String (256)
login_verification_token_expires: DateTime
created_at: DateTime
```

### World
```python
world_id: String (32 karakter, UUID hex)
name: String (120)
```

### Card
```python
id: String (32 karakter, UUID hex)
world_id: String (32)
owner_id: String (32)
name: String (16)
picture: LargeBinary (opcionális)
health: Integer
damage: Integer
type: String (6)
position: Integer
is_leader: Boolean
```

### Dungeon
```python
id: String (32 karakter, UUID hex)
name: String (120)
world_id: String (32)
list_of_card_ids: JSON lista
```

---

## Konfiguráció

A `backend/config.py`-ban van a konfig. Három környezet:
- **development** (alapértelmezett): DEBUG be, SQLite
- **production**: DEBUG ki
- **testing**: külön test.db adatbázis

JWT token lejárati idő:
- Access token: 1 óra (de a `generate_token()` függvényben ez átírható)
- Refresh token: 30 nap (nincs még implementálva)

E-mail konfig (`backend/app/email_config.py`):
- SMTP: `smtp.dreamhost.com:587` (TLS)
- Token lejárat: 24 óra

---

## Biztonság

- Jelszavak bcrypt-tel hash-elve (rounds alapértelmezett: 12)
- JWT tokenek HS256 algoritmussal
- CORS csak megadott originokra engedélyezett
- Rate limiting az összes endpointra
- E-mail verifikáció kapcsolható

**Figyelem:** Az `SECRET_KEY` és `JWT_SECRET_KEY` éles környezetben legyen rendesen generálva, ne használd a default értékeket!

---


## Fejlesztés / Hozzájárulás

Ha hibát találsz vagy jobb ötleted van, nyiss issue-t vagy küldj PR-t. A kód nem tökéletes, de működik, és ez a lényeg.

---

## Licensz

Nincs licensz megadva, szóval... használd szabadon? Ha valami fontosba akarod rakni, akkor írj előtte. :)

---

## Kapcsolat

Ha kérdésed van vagy csak beszélgetni akarsz róla, keress nyugodtan GitHubon vagy az e-mail címen amit a commitokban látsz.

