"""
IoT climate sensor simulator for TerraPulse.

This script stands in for real IoT sensors we don't have yet. Every second it
makes up methane / smoke / temperature readings for 10 Indian regions and
publishes them to Kafka topic "iot-climate-stream". Most ticks look normal;
about 5% of the time a region "spikes" like a fire event so downstream
consumers (alerts, dashboards) have something dramatic to react to.
"""

from __future__ import annotations

import json
import signal
import sys
import time
from datetime import datetime, timezone

from kafka import KafkaProducer
from kafka.errors import KafkaError

BOOTSTRAP_SERVERS = "localhost:9092"
TOPIC = "iot-climate-stream"
TICK_SECONDS = 1.0
FIRE_CHANCE = 0.05

REGIONS = [
    "Delhi",
    "Mumbai",
    "Chennai",
    "Bengaluru",
    "Kolkata",
    "Jaipur",
    "Nagpur",
    "Patna",
    "Lucknow",
    "Ahmedabad",
]

_running = True


def _handle_shutdown(signum, frame) -> None:  # noqa: ARG001
    global _running
    _running = False


def _build_reading(region: str, rng) -> tuple[dict, bool]:
    """Return (payload, is_fire_event) for one region."""
    is_fire = rng.random() < FIRE_CHANCE

    if is_fire:
        methane = float(rng.uniform(400, 600))
        smoke = float(rng.uniform(300, 500))
        temperature = float(rng.uniform(45, 55))
    else:
        methane = float(rng.uniform(0, 100))
        smoke = float(rng.uniform(0, 100))
        temperature = float(rng.uniform(20, 40))

    payload = {
        "region_name": region,
        "methane_level": round(methane, 2),
        "smoke_density": round(smoke, 2),
        "temperature": round(temperature, 2),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    return payload, is_fire


def main() -> int:
    import numpy as np

    # Windows terminals often default to cp1252; allow emoji / unicode logs.
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")

    signal.signal(signal.SIGINT, _handle_shutdown)
    if hasattr(signal, "SIGTERM"):
        signal.signal(signal.SIGTERM, _handle_shutdown)

    print(f"Connecting to Kafka at {BOOTSTRAP_SERVERS} ...", flush=True)
    try:
        producer = KafkaProducer(
            bootstrap_servers=BOOTSTRAP_SERVERS,
            acks=1,
            retries=3,
        )
    except KafkaError as exc:
        print(f"Could not connect to Kafka: {exc}", file=sys.stderr, flush=True)
        return 1

    rng = np.random.default_rng()
    print(
        f"Publishing to topic '{TOPIC}' every {TICK_SECONDS:.0f}s. Ctrl+C to stop.",
        flush=True,
    )

    try:
        while _running:
            tick_start = time.monotonic()
            for region in REGIONS:
                if not _running:
                    break
                payload, is_fire = _build_reading(region, rng)
                try:
                    future = producer.send(
                        TOPIC,
                        key=region.encode("utf-8"),
                        value=json.dumps(payload).encode("utf-8"),
                    )
                    future.get(timeout=5)
                except KafkaError as exc:
                    print(f"ERROR sending {region}: {exc}", file=sys.stderr, flush=True)
                    continue

                if is_fire:
                    print(
                        f"🔥 FIRE EVENT  {region}: methane={payload['methane_level']} "
                        f"smoke={payload['smoke_density']} temp={payload['temperature']}",
                        flush=True,
                    )
                else:
                    print(
                        f"sent {region}: methane={payload['methane_level']} "
                        f"smoke={payload['smoke_density']} temp={payload['temperature']}",
                        flush=True,
                    )

            elapsed = time.monotonic() - tick_start
            remaining = TICK_SECONDS - elapsed
            if remaining > 0 and _running:
                time.sleep(remaining)
    finally:
        producer.flush(timeout=5)
        producer.close()
        print("Simulator stopped. Kafka producer closed cleanly.", flush=True)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
