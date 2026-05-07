import requests
from datetime import datetime, timezone
from venues import VENUES

OUTDOOR_LEAGUES = {"NFL", "MLB", "EPL", "UCL", "CFB"}

WMO_LABELS = {
    0: "clear", 1: "clear", 2: "cloudy", 3: "cloudy",
    45: "fog", 48: "fog",
    51: "drizzle", 53: "drizzle", 55: "drizzle",
    56: "drizzle", 57: "drizzle",
    61: "rain", 63: "rain", 65: "rain",
    66: "rain", 67: "rain",
    71: "snow", 73: "snow", 75: "snow", 77: "snow",
    80: "rain", 81: "rain", 82: "rain",
    85: "snow", 86: "snow",
    95: "storm", 96: "storm", 99: "storm",
}

RETRACTABLE = {
    "ARI_NFL", "ATL_NFL", "DAL_NFL", "HOU_NFL", "IND_NFL",
    "LAC_NFL", "LAR_NFL",
    "ARI_MLB", "HOU_MLB", "MIA_MLB", "MIL_MLB", "SEA_MLB",
    "TEX_MLB", "TOR_MLB",
}

_cache = {}
_CACHE_TTL = 3600


def _format_summary(weather):
    if not weather:
        return ""
    parts = [f"{weather['temp_f']}°F"]
    label = weather.get("label", "clear")
    if label in ("rain", "drizzle", "snow", "storm") and weather.get("precip_pct"):
        parts.append(f"{weather['precip_pct']}% {label}")
    elif label != "clear":
        parts.append(label)
    if weather.get("wind_mph", 0) >= 10:
        parts.append(f"{weather['wind_mph']} mph wind")
    return " · ".join(parts)


def get_game_weather(home_abbr, league, game_iso, venue_indoor=False):
    if league not in OUTDOOR_LEAGUES:
        return None

    key = f"{home_abbr}_{league}" if not home_abbr.endswith(f"_{league}") else home_abbr

    if venue_indoor or key in RETRACTABLE:
        return None

    venue = VENUES.get(key)
    if not venue:
        return None

    try:
        game_dt = datetime.fromisoformat(game_iso.replace("Z", "+00:00"))
    except Exception:
        return None

    now = datetime.now(timezone.utc)
    delta_days = (game_dt - now).total_seconds() / 86400
    if delta_days > 15 or delta_days < -1:
        return None

    cache_key = (key, game_dt.strftime("%Y-%m-%dT%H"))
    cached = _cache.get(cache_key)
    if cached and cached["expires"] > now.timestamp():
        return cached["data"]

    try:
        resp = requests.get(
            "https://api.open-meteo.com/v1/forecast",
            params={
                "latitude": venue["lat"],
                "longitude": venue["lon"],
                "hourly": "temperature_2m,precipitation_probability,wind_speed_10m,weather_code",
                "temperature_unit": "fahrenheit",
                "wind_speed_unit": "mph",
                "timezone": "UTC",
                "past_days": 1,
                "forecast_days": 16,
            },
            timeout=5,
        )
        if not resp.ok:
            return None
        data = resp.json()
    except Exception:
        return None

    hourly = data.get("hourly", {})
    times = hourly.get("time", [])
    if not times:
        return None

    target_prefix = game_dt.strftime("%Y-%m-%dT%H")
    idx = None
    for i, t in enumerate(times):
        if t.startswith(target_prefix):
            idx = i
            break
    if idx is None:
        return None

    try:
        temp = round(hourly["temperature_2m"][idx])
        precip_raw = hourly["precipitation_probability"][idx]
        precip = int(precip_raw) if precip_raw is not None else 0
        wind = round(hourly["wind_speed_10m"][idx])
        code = hourly["weather_code"][idx]
        label = WMO_LABELS.get(code, "clear")
    except (IndexError, KeyError, TypeError):
        return None

    result = {
        "temp_f": temp,
        "precip_pct": precip,
        "wind_mph": wind,
        "label": label,
    }
    result["summary"] = _format_summary(result)

    _cache[cache_key] = {
        "data": result,
        "expires": now.timestamp() + _CACHE_TTL,
    }

    return result
