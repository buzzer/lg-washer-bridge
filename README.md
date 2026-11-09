# ThinQ → MQTT Bridge

Bindet den LG-Waschtrockner (ThinQ Connect API, cloudbasiert) an MQTT an.

## Topics (Prefix `lg`)

| Topic | Inhalt |
|---|---|
| `lg/bridge/status` | `online` / `offline` (Last Will) |
| `lg/<deviceId>/info` | Alias, Typ, Modell (retained) |
| `lg/<deviceId>/state` | Gerätestatus als JSON (retained), Abfrage alle 60 s |
| `lg/<deviceId>/set` | JSON-Befehl, wird an die ThinQ-Control-API weitergereicht |

## Installation (Raspberry Pi)

```
cp .env.example .env   # THINQ_PAT eintragen (Token von connect-pat.lgthinq.com)
chmod 600 .env
docker compose up -d --build
docker logs -f thinq-bridge
```

Der Token liegt nur in `.env` (nicht im Git).
