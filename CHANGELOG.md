# Changelog

## 0.1.0 - 2026-11-09

First public release.

### Added
- LG ThinQ Connect to MQTT bridge: polls all devices of the LG account and
  publishes their state as retained JSON (`<prefix>/state/<deviceId>`).
- Device info topic (`<prefix>/info/<deviceId>`) and availability topic
  (`<prefix>/status`, with last will).
- Command forwarding from `<prefix>/set/<deviceId>` to the ThinQ control
  endpoint (untested against real hardware).
- Docker image running as an unprivileged user, with a healthcheck based on
  the last successful poll.
- Configuration via environment variables (`.env.example`).
- README with setup, configuration, topics, security notes and disclaimer.
- MIT license, GitHub Actions CI (ruff, Docker build) and Dependabot.
