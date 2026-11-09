"""LG ThinQ Connect -> MQTT bridge.

Polls all devices of the LG account via the official ThinQ Connect API and
publishes their state as retained JSON to MQTT. Commands can be sent as JSON
to ``<prefix>/set/<device_id>`` and are forwarded to the control endpoint.
"""
import asyncio
import json
import logging
import os
import signal
import time
import uuid

import aiohttp
import paho.mqtt.client as mqtt
from thinqconnect.thinq_api import ThinQApi, ThinQAPIException

log = logging.getLogger("thinq-bridge")

# Touched after every successful poll; used by the container healthcheck.
HEALTH_FILE = "/tmp/healthy"

TOKEN = os.environ["THINQ_PAT"]
COUNTRY = os.environ.get("THINQ_COUNTRY", "DE")
POLL_INTERVAL = int(os.environ.get("POLL_INTERVAL", "60"))
MQTT_HOST = os.environ.get("MQTT_HOST", "localhost")
MQTT_PORT = int(os.environ.get("MQTT_PORT", "1883"))
MQTT_USER = os.environ.get("MQTT_USER")
MQTT_PASSWORD = os.environ.get("MQTT_PASSWORD")
PREFIX = os.environ.get("MQTT_PREFIX", "washer").rstrip("/")
# Stable client id so LG does not see a new client on every restart.
CLIENT_ID = os.environ.get(
    "THINQ_CLIENT_ID", str(uuid.uuid5(uuid.NAMESPACE_DNS, "waschtrockner-bridge"))
)


async def main() -> None:
    loop = asyncio.get_running_loop()
    stop = asyncio.Event()
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, stop.set)

    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    if MQTT_USER:
        client.username_pw_set(MQTT_USER, MQTT_PASSWORD)
    client.will_set(f"{PREFIX}/status", "offline", retain=True)

    async with aiohttp.ClientSession() as session:
        api = ThinQApi(session, TOKEN, COUNTRY, CLIENT_ID)

        def on_connect(c, _u, _f, rc, _p):
            log.info("MQTT connected: %s", rc)
            c.publish(f"{PREFIX}/status", "online", retain=True)
            c.subscribe(f"{PREFIX}/set/+")

        def on_message(_c, _u, msg):
            device_id = msg.topic.split("/")[-1]
            try:
                payload = json.loads(msg.payload)
            except ValueError:
                log.warning("Ignoring non-JSON command on %s", msg.topic)
                return
            asyncio.run_coroutine_threadsafe(send_command(api, device_id, payload), loop)

        client.on_connect = on_connect
        client.on_message = on_message
        client.connect_async(MQTT_HOST, MQTT_PORT)
        client.loop_start()

        try:
            while not stop.is_set():
                await poll_once(api, client)
                try:
                    await asyncio.wait_for(stop.wait(), POLL_INTERVAL)
                except asyncio.TimeoutError:
                    pass
        finally:
            client.publish(f"{PREFIX}/status", "offline", retain=True).wait_for_publish(5)
            client.loop_stop()
            client.disconnect()


async def poll_once(api: ThinQApi, client: mqtt.Client) -> None:
    try:
        devices = await api.async_get_device_list() or []
        for dev in devices:
            device_id = dev["deviceId"]
            info = dev.get("deviceInfo", {})
            try:
                state = await api.async_get_device_status(device_id)
            except ThinQAPIException as exc:
                # e.g. stale devices still listed in the account
                log.warning("Skipping %s (%s): %s", info.get("alias"), device_id, exc)
                continue
            client.publish(
                f"{PREFIX}/info/{device_id}",
                json.dumps({"alias": info.get("alias"), "type": info.get("deviceType"),
                            "model": info.get("modelName")}),
                retain=True,
            )
            client.publish(f"{PREFIX}/state/{device_id}", json.dumps(state), retain=True)
            log.info("Published state of %s (%s)", info.get("alias"), device_id)
        with open(HEALTH_FILE, "w") as fh:
            fh.write(str(time.time()))
    except ThinQAPIException as exc:
        log.error("ThinQ API error: %s", exc)
    except (aiohttp.ClientError, asyncio.TimeoutError) as exc:
        log.error("Network error: %s", exc)


async def send_command(api: ThinQApi, device_id: str, payload: dict) -> None:
    try:
        await api.async_post_device_control(device_id, payload)
        log.info("Command sent to %s: %s", device_id, payload)
    except Exception as exc:  # keep the bridge alive on any command failure
        log.error("Command for %s failed: %s", device_id, exc)


if __name__ == "__main__":
    logging.basicConfig(level=os.environ.get("LOG_LEVEL", "INFO"),
                        format="%(asctime)s %(levelname)s %(message)s")
    asyncio.run(main())
