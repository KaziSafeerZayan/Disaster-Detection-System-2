"""Public weather, river-model and report discovery for an experimental flood screen."""
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from functools import lru_cache
import math
import re
import xml.etree.ElementTree as ET

import numpy as np
import requests
from sklearn.feature_extraction.text import HashingVectorizer


WEATHER_POLL_SECONDS = 120
RIVER_POLL_SECONDS = 900
REPORT_POLL_SECONDS = 600
USER_AGENT = "FlooderLocalPrototype/1.0 (+https://github.com/KaziSafeerZayan/Disaster-Detection-System)"


def utc_time(value):
    parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    return parsed.replace(tzinfo=timezone.utc) if parsed.tzinfo is None else parsed.astimezone(timezone.utc)


def _get(url, params=None):
    response = requests.get(url, params=params, timeout=(3, 7), headers={"User-Agent": USER_AGENT})
    response.raise_for_status()
    return response


def _number(value):
    return float(value) if isinstance(value, (int, float)) and math.isfinite(value) else None


def _sum_window(rows, start, end, minimum=24):
    values = [value for timestamp, value in rows if start < timestamp <= end and value is not None]
    return round(sum(values), 2) if len(values) >= minimum else None


def parse_weather(payload, now):
    current, hourly = payload.get("current", {}), payload.get("hourly", {})
    valid_at = utc_time(current["time"])
    if abs((now - valid_at).total_seconds()) > 10800:
        raise ValueError("Weather model valid time is more than three hours from now.")
    times = [utc_time(t) for t in hourly.get("time", [])]
    rain = list(zip(times, map(_number, hourly.get("precipitation", []))))
    probabilities = [_number(v) for t, v in zip(times, hourly.get("precipitation_probability", []))
                     if now < t <= now + timedelta(hours=24) and _number(v) is not None]
    soil = [_number(v) for t, v in zip(times, hourly.get("soil_moisture_0_to_1cm", []))
            if t <= now and _number(v) is not None]
    return {
        "source": "Open-Meteo weather models", "kind": "model estimate / forecast",
        "valid_at": valid_at.isoformat(), "temperature_c": _number(current.get("temperature_2m")),
        "humidity_pct": _number(current.get("relative_humidity_2m")),
        "rain_current_mm": _number(current.get("precipitation")),
        "rain_interval_seconds": current.get("interval", 900),
        "rain_past24_mm": _sum_window(rain, now - timedelta(hours=24), now),
        "rain_next24_mm": _sum_window(rain, now, now + timedelta(hours=24)),
        "max_rain_probability_pct": max(probabilities) if probabilities else None,
        "soil_moisture": soil[-1] if soil else None,
        "grid_lat": payload.get("latitude"), "grid_lon": payload.get("longitude"),
        "source_url": "https://open-meteo.com/en/docs",
    }


def parse_met_weather(payload, now):
    properties = payload["properties"]
    updated = utc_time(properties["meta"]["updated_at"])
    if (now - updated).total_seconds() > 21600:
        raise ValueError("Backup weather forecast is older than six hours.")
    rows = properties["timeseries"]
    current = min(rows, key=lambda row: abs((utc_time(row["time"]) - now).total_seconds()))
    instant = current["data"]["instant"]["details"]
    amounts = [row["data"].get("next_1_hours", {}).get("details", {}).get("precipitation_amount")
               for row in rows if now <= utc_time(row["time"]) < now + timedelta(hours=25)]
    amounts = [_number(value) for value in amounts[:24] if _number(value) is not None]
    return {
        "source": "MET Norway Locationforecast", "kind": "forecast (backup source)",
        "valid_at": current["time"], "issued_at": updated.isoformat(),
        "temperature_c": _number(instant.get("air_temperature")),
        "humidity_pct": _number(instant.get("relative_humidity")),
        "rain_current_mm": None, "rain_interval_seconds": 3600,
        "rain_past24_mm": None, "rain_next24_mm": round(sum(amounts), 2) if len(amounts) == 24 else None,
        "max_rain_probability_pct": None, "soil_moisture": None,
        "source_url": "https://api.met.no/weatherapi/locationforecast/2.0/documentation",
    }


@lru_cache(maxsize=64)
def fetch_weather(latitude, longitude, poll_bucket):
    now = datetime.now(timezone.utc)
    errors = []
    try:
        payload = _get("https://api.open-meteo.com/v1/forecast", {
            "latitude": latitude, "longitude": longitude, "timezone": "UTC",
            "current": "temperature_2m,relative_humidity_2m,precipitation,rain,weather_code",
            "hourly": "precipitation,precipitation_probability,soil_moisture_0_to_1cm",
            "past_days": 3, "forecast_days": 3,
        }).json()
        result = parse_weather(payload, now)
    except (requests.RequestException, KeyError, ValueError) as exc:
        errors.append(type(exc).__name__)
        try:
            payload = _get("https://api.met.no/weatherapi/locationforecast/2.0/compact", {
                "lat": round(latitude, 4), "lon": round(longitude, 4),
            }).json()
            result = parse_met_weather(payload, now)
        except (requests.RequestException, KeyError, ValueError) as backup:
            raise RuntimeError("Both real weather sources are unavailable; retrying automatically.") from backup
    result["fetched_at"] = now.isoformat()
    result["backup_used"] = bool(errors)
    return result


def parse_river(payload, now):
    daily = payload["daily"]
    rows = {day: _number(value) for day, value in zip(daily["time"], daily["river_discharge"])}
    today = now.date()
    current = rows.get(today.isoformat())
    if current is None:
        raise ValueError("River forecast does not cover today.")
    future = [rows.get((today + timedelta(days=i)).isoformat()) for i in (1, 2, 3)]
    peak = max(future) if all(value is not None for value in future) else None
    previous = [value for day, value in rows.items() if today - timedelta(days=30) <= datetime.fromisoformat(day).date() < today and value is not None]
    return {
        "source": "Copernicus GloFAS via Open-Meteo", "kind": "modelled discharge, not a river gauge",
        "valid_date": today.isoformat(), "discharge_m3s": current, "peak_next3_m3s": peak,
        "change_next3_pct": (peak / current - 1) * 100 if peak is not None and current > 0 else None,
        "past30_p75_m3s": float(np.percentile(previous, 75)) if len(previous) >= 20 else None,
        "grid_lat": payload.get("latitude"), "grid_lon": payload.get("longitude"),
        "source_url": "https://open-meteo.com/en/docs/flood-api",
    }


@lru_cache(maxsize=64)
def fetch_river(latitude, longitude, poll_bucket):
    now = datetime.now(timezone.utc)
    payload = _get("https://flood-api.open-meteo.com/v1/flood", {
        "latitude": latitude, "longitude": longitude, "daily": "river_discharge",
        "past_days": 30, "forecast_days": 7,
    }).json()
    result = parse_river(payload, now)
    result["fetched_at"] = now.isoformat()
    return result


def distance_km(a_lat, a_lon, b_lat, b_lon):
    lat1, lat2 = math.radians(a_lat), math.radians(b_lat)
    delta_lat, delta_lon = lat2 - lat1, math.radians(b_lon - a_lon)
    value = math.sin(delta_lat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(delta_lon / 2) ** 2
    return 6371 * 2 * math.asin(min(1, math.sqrt(value)))


def text_similarity(query, documents):
    """A lightweight sparse text-vector experiment, not a trained risk classifier."""
    if not documents:
        return []
    vectorizer = HashingVectorizer(n_features=2048, alternate_sign=False, ngram_range=(1, 2), norm="l2")
    vectors = vectorizer.transform([query, *documents])
    return (vectors[1:] @ vectors[0].T).toarray().ravel().tolist()


def parse_reports(xml, latitude, longitude, region, now):
    if len(xml) > 2_000_000:
        raise ValueError("Report feed is larger than expected.")
    namespaces = {"g": "http://www.gdacs.org", "geo": "http://www.georss.org/georss"}
    root = ET.fromstring(xml)
    candidates, examined = [], 0
    for item in root.findall("./channel/item"):
        if item.findtext("g:eventtype", namespaces=namespaces) != "FL":
            continue
        examined += 1
        try:
            ended = parsedate_to_datetime(item.findtext("g:todate", namespaces=namespaces))
            modified = parsedate_to_datetime(item.findtext("g:datemodified", namespaces=namespaces) or item.findtext("pubDate"))
            if ended < now - timedelta(days=7) or modified < now - timedelta(days=7) or modified > now + timedelta(hours=6):
                continue
            point = item.findtext("geo:point", namespaces=namespaces).split()
            distance = distance_km(latitude, longitude, float(point[0]), float(point[1]))
            if distance > 100:
                continue
            text = re.sub(r"<[^>]+>", " ", (item.findtext("title") or "") + " " + (item.findtext("description") or ""))
            candidates.append({"title": item.findtext("title"), "text": text,
                               "url": item.findtext("link"), "updated_at": modified.isoformat(),
                               "alert_level": item.findtext("g:alertlevel", namespaces=namespaces),
                               "distance_km": distance})
        except (TypeError, ValueError, AttributeError):
            continue
    scores = text_similarity(f"{region} flood heavy rainfall river warning", [item["text"] for item in candidates])
    for item, score in zip(candidates, scores):
        item["retrieval_similarity"] = score
    candidates.sort(key=lambda item: item["retrieval_similarity"], reverse=True)
    return {"source": "GDACS public flood reports", "examined": examined, "nearby": candidates,
            "radius_km": 100, "fetched_at": now.isoformat(), "source_url": "https://www.gdacs.org/xml/rss.xml"}


@lru_cache(maxsize=32)
def _report_feed(poll_bucket):
    return _get("https://www.gdacs.org/xml/rss.xml").content


def fetch_reports(latitude, longitude, region, poll_bucket):
    return parse_reports(_report_feed(poll_bucket), latitude, longitude, region, datetime.now(timezone.utc))


def screen_conditions(weather=None, river=None, reports=None):
    """Transparent experimental conditions, never a calibrated flood probability."""
    alerts = (reports or {}).get("nearby", [])
    if any((item.get("alert_level") or "").lower() in ("red", "orange") for item in alerts):
        return {"level": "PUBLISHED FLOOD ALERT NEARBY", "reason": "A fresh orange/red GDACS flood event is reported within 100 km; check its location and official advice."}
    if not weather and not river:
        return {"level": "UNKNOWN", "reason": "Real numerical inputs are unavailable; no flood assessment can be made."}
    rain_past = weather.get("rain_past24_mm") if weather else None
    rain_next = weather.get("rain_next24_mm") if weather else None
    rain_values = [value for value in (rain_past, rain_next) if value is not None]
    rising = river and river.get("change_next3_pct") is not None and river["change_next3_pct"] >= 20
    elevated_flow = river and river.get("past30_p75_m3s") is not None and river["discharge_m3s"] >= river["past30_p75_m3s"]
    if rain_values and max(rain_values) > 88:
        return {"level": "ELEVATED RAINFALL SIGNAL", "reason": "Past or forecast 24-hour model rainfall exceeds 88 mm. This is a screening signal, not a flood probability."}
    if (rain_values and max(rain_values) >= 44) or (rising and elevated_flow):
        return {"level": "WATCH", "reason": "Heavy model rainfall (44+ mm/24 h), or a rising river forecast above its recent 75th percentile, warrants closer checking."}
    if not rain_values:
        return {"level": "LIMITED DATA", "reason": "Rainfall coverage is incomplete; river context alone cannot establish local flood likelihood."}
    return {"level": "NO ELEVATED SIGNAL IN AVAILABLE DATA", "reason": "Available rainfall and discharge forecasts do not trigger the prototype rules. This does not establish that the area is flood-free."}
