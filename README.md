# LG Washer Bridge (ThinQ → MQTT)

Small Docker service that publishes the state of LG ThinQ appliances (tested
with a washer-dryer, model `WTHT3`, type `DEVICE_WASHER`) to MQTT and
forwards commands back. It uses the official **LG ThinQ Connect API**
(cloud-based; there is no local API) via the `thinqconnect` SDK.

## How it works

```
LG ThinQ cloud  <--REST (poll every 60 s)--  bridge  --publish-->  MQTT broker  -->  Node-RED / others
                <--control (washer/set)----          <--subscribe--
```

The device IP is not needed. The appliance must be set up in the LG ThinQ app.

## Setup

1. Create a Personal Access Token at <https://connect-pat.lgthinq.com> (same
   LG account as the app; permissions: device list, device status, device control).
2. Configure and start:
   ```
   cp .env.example .env     # fill in THINQ_PAT, MQTT_HOST, ...
   chmod 600 .env
   docker compose up -d --build
   docker logs -f thinq-bridge
   ```

### Configuration (`.env`)

| Variable | Default | Meaning |
|---|---|---|
| `THINQ_PAT` | – (required) | Personal access token |
| `THINQ_COUNTRY` | `DE` | Country code of the LG account (selects API region) |
| `POLL_INTERVAL` | `60` | Seconds between polls |
| `MQTT_HOST` / `MQTT_PORT` | `localhost` / `1883` | Broker |
| `MQTT_USER` / `MQTT_PASSWORD` | unset | Optional broker credentials |
| `MQTT_PREFIX` | `washer` | Topic prefix |
| `THINQ_CLIENT_ID` | derived, stable | Client id sent to LG |
| `LOG_LEVEL` | `INFO` | Python log level |

## MQTT topics

| Topic | Payload |
|---|---|
| `washer/status` | `online` / `offline` (last will) |
| `washer/info/<deviceId>` | `{"alias": "...", "type": "DEVICE_WASHER", "model": "WTHT3"}` (retained) |
| `washer/state/<deviceId>` | Device state JSON (retained), refreshed every poll |
| `washer/set/<deviceId>` | JSON command, sent to the ThinQ control endpoint |

Example state (note: the API returns a **list** with one object):

```json
[{"runState": {"currentState": "POWER_OFF"},
  "timer": {"remainHour": 0, "remainMinute": 28, "totalHour": 0, "totalMinute": 28,
            "relativeHourToStop": 0, "relativeMinuteToStop": 0},
  "remoteControlEnable": {"remoteControlEnabled": false},
  "location": {"locationName": "MAIN"}}]
```

The device id is a 64-character hex string; list it with
`mosquitto_sub -h <broker> -t 'washer/info/#' -v`.

### Node-RED

Use an `mqtt in` node on `washer/state/#` and read `msg.payload[0].runState.currentState`
(JSON mode, parse to object).

## Notes and limitations

- Cloud only: no internet or an LG outage means no data.
- Commands (`washer/set/...`) need "remote start" enabled on the appliance and
  are untested; the payload format is defined by the ThinQ Connect API.
- Stale devices that are still listed in the LG account
  (`ALREADY_DEVICE_DELETED`) are skipped with a warning.
- The token lives only in `.env`, which is git-ignored. Never commit it.

## Security

- Anyone who can publish to `washer/set/<deviceId>` can control the appliance.
  The default configuration assumes a trusted broker; for anything else
  enable authentication (`MQTT_USER` / `MQTT_PASSWORD`) and topic ACLs on the
  broker, and do not expose it to the internet.
- The container runs as an unprivileged user.

## Disclaimer

This is an unofficial project and is not affiliated with or endorsed by LG
Electronics. LG and ThinQ are trademarks of LG Electronics. Use at your own
risk (see [LICENSE](LICENSE)).

## License

[MIT](LICENSE)
