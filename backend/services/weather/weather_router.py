"""
Weather overlay for MDT/CAD/HEMS. Fetches from Open-Meteo (no API key).
Used by WeatherOverlay component on CAD dashboard and HEMS.
"""
from __future__ import annotations

import logging
from typing import Any

import httpx
from fastapi import APIRouter, HTTPException, Query

logger = logging.getLogger(__name__)

OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"

router = APIRouter(prefix="/api/weather", tags=["Weather"])


def _weather_code_to_label(code: int) -> str:
    """WMO weather code to short label."""
    if code == 0:
        return "Clear"
    if code in (1, 2, 3):
        return "Partly cloudy"
    if code in (45, 48):
        return "Fog"
    if code in (51, 53, 55, 56, 57):
        return "Drizzle"
    if code in (61, 63, 65, 66, 67):
        return "Rain"
    if code in (71, 73, 75, 77):
        return "Snow"
    if code in (80, 81, 82):
        return "Showers"
    if code in (95, 96, 99):
        return "Thunderstorm"
    return "Cloudy"


@router.get("/current")
def get_current_weather(
    lat: float = Query(..., ge=-90, le=90),
    lng: float = Query(..., ge=-180, le=180),
) -> dict[str, Any]:
    """
    Current weather for a lat/lng (e.g. MDT map center or incident). Uses Open-Meteo (no key).
    """
    params = {
        "latitude": lat,
        "longitude": lng,
        "current": "temperature_2m,relative_humidity_2m,weather_code,wind_speed_10m,wind_direction_10m,cloud_cover,visibility",
        "timezone": "auto",
    }
    try:
        with httpx.Client(timeout=10.0) as client:
            r = client.get(OPEN_METEO_URL, params=params)
            r.raise_for_status()
            data = r.json()
    except httpx.HTTPError as e:
        logger.warning("Open-Meteo request failed: %s", e)
        raise HTTPException(status_code=502, detail="Weather service unavailable") from e

    current = data.get("current") or {}
    code = int(current.get("weather_code", 0))
    return {
        "temperature_c": current.get("temperature_2m"),
        "temperature_f": round(current.get("temperature_2m", 0) * 9 / 5 + 32, 1) if current.get("temperature_2m") is not None else None,
        "relative_humidity": current.get("relative_humidity_2m"),
        "weather_code": code,
        "conditions": _weather_code_to_label(code),
        "wind_speed_kmh": current.get("wind_speed_10m"),
        "wind_speed_mph": round(current.get("wind_speed_10m", 0) * 0.621371, 1) if current.get("wind_speed_10m") is not None else None,
        "wind_direction": current.get("wind_direction_10m"),
        "cloud_cover": current.get("cloud_cover"),
        "visibility_km": current.get("visibility"),
        "latitude": lat,
        "longitude": lng,
    }
