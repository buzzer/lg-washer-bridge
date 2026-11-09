# ThinQ → MQTT Bridge

Bindet den LG-Waschtrockner (ThinQ Connect API, cloudbasiert) an MQTT an.

## Topics (Prefix `washer`)

| Topic | Inhalt |
|---|---|
| `washer/status` | `online` / `offline` (Last Will) |
| `washer/info/<deviceId>` | Alias, Typ, Modell (retained) |
| `washer/state/<deviceId>` | Gerätestatus als JSON (retained), Abfrage alle 60 s |
| `washer/set/<deviceId>` | JSON-Befehl, wird an die ThinQ-Control-API weitergereicht |

## Installation (Raspberry Pi)

```
cp .env.example .env   # THINQ_PAT eintragen (Token von connect-pat.lgthinq.com)
chmod 600 .env
docker compose up -d --build
docker logs -f thinq-bridge
```

Der Token liegt nur in `.env` (nicht im Git).
