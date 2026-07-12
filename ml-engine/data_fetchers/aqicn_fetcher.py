"""
Live AQI fetcher for the current reading of a city via the AQICN / WAQI API.

We keep this separate from historical data because AQICN only returns the
latest snapshot for a feed — it does not provide past daily AQI series.
Historical (or training) time series are therefore a different concern;
for now that role is filled by synthetic seasonal data.
"""

from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import Any

import requests
from dotenv import load_dotenv

load_dotenv()


class InvalidCityError(Exception):
    """Raised when AQICN returns a non-ok status for the requested city."""


class AQIFetchError(Exception):
    """Raised when the AQICN request fails due to network or timeout errors."""


class ConfigError(Exception):
    """Raised when required configuration (AQICN_API_TOKEN) is missing."""


_API_TOKEN = os.getenv("AQICN_API_TOKEN")
if not _API_TOKEN:
    raise ConfigError(
        "AQICN_API_TOKEN is missing. Set it in ml-engine/.env before fetching live AQI."
    )

_BASE_URL = "https://api.waqi.info/feed/{city}/"
_REQUEST_TIMEOUT_SEC = 15


def _as_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _as_int(value: Any) -> int | None:
    if value is None:
        return None
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return None


def get_city_aqi(city: str) -> dict:
    """
    Fetch the current AQI snapshot for a city from AQICN.

    Returns a dict with city, pm25, pm10, no2, aqi, and an ISO timestamp.
    """
    url = _BASE_URL.format(city=city)
    try:
        response = requests.get(
            url,
            params={"token": _API_TOKEN},
            timeout=_REQUEST_TIMEOUT_SEC,
        )
        response.raise_for_status()
        payload = response.json()
    except (requests.Timeout, requests.ConnectionError) as exc:
        raise AQIFetchError(f"Failed to reach AQICN for city '{city}': {exc}") from exc
    except requests.RequestException as exc:
        raise AQIFetchError(f"AQICN request failed for city '{city}': {exc}") from exc

    if payload.get("status") != "ok":
        raise InvalidCityError(
            f"AQICN rejected city '{city}' (status={payload.get('status')!r})."
        )

    data = payload.get("data") or {}
    iaqi = data.get("iaqi") or {}

    time_info = data.get("time") or {}
    iso = time_info.get("iso")
    if not iso:
        iso = datetime.now(timezone.utc).isoformat()

    return {
        "city": city,
        "pm25": _as_float((iaqi.get("pm25") or {}).get("v")),
        "pm10": _as_float((iaqi.get("pm10") or {}).get("v")),
        "no2": _as_float((iaqi.get("no2") or {}).get("v")),
        "aqi": _as_int(data.get("aqi")),
        "timestamp": iso,
    }
