# Docker Setup for Damareen

Ez a mappa tartalmazza a Docker konfigurációkat.

## Fájlok

- `Dockerfile.backend` - Python/Flask backend
- `Dockerfile.frontend` - PHP frontend
- `supervisord.conf` - Supervisor config (ha egy containerben futtatod mindkettőt)

## Használat

### Opció 1: Egy container (mindkettő együtt)

A project root-ból:
```bash
docker-compose up -d
```

Ez a fő `Dockerfile`-t használja ami supervisord-al futtatja mindkét szolgáltatást.

### Opció 2: Külön containerek (ajánlott)

```bash
docker-compose -f docker-compose.separated.yml up -d
```

Ez építi a `Dockerfile.backend` és `Dockerfile.frontend` alapján külön containereket.

## Logs

```bash
# Mindkét service log-jai
docker-compose logs -f

# Csak backend
docker-compose logs -f backend

# Csak frontend
docker-compose logs -f frontend
```

## Leállítás

```bash
docker-compose down

# Volume törlésével együtt (DB is törlődik!)
docker-compose down -v
```

## Troubleshooting

**Port már használatban van:**
```bash
# Nézd meg mi fut a portokon
lsof -i :7621
lsof -i :8000

# Vagy változtasd meg a portokat a docker-compose.yml-ben
```

**DB nem perzisztálódik:**
A volume automatikusan létrejön, de ha törölted:
```bash
docker volume ls
docker volume inspect damareen_damareen-db
```

**Rebuild szükséges kód változtatás után:**
```bash
docker-compose up -d --build
```
