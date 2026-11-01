"""Nonblocking ten-second monitoring; slow satellite reads cannot stall the stream."""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import math

from config import GLOBAL_REGIONS
from src.weather_sources import (
    WEATHER_POLL_SECONDS, RIVER_POLL_SECONDS, REPORT_POLL_SECONDS,
    fetch_weather, fetch_river, fetch_reports, screen_conditions, utc_time,
)


_EXECUTOR = ThreadPoolExecutor(max_workers=4, thread_name_prefix="flooder-monitor")
UI_REFRESH_SECONDS = 10


def _poll(slot, function, interval, now_seconds):
    future = slot.get("future")
    if future is not None and future.done():
        slot["completed"] = True
        try:
            slot["data"] = future.result()
            slot["error"] = None
        except Exception as exc:
            slot["error"] = str(exc)
        slot["future"] = None
    retry = min(interval, 30) if slot.get("error") else interval
    if slot.get("future") is None and now_seconds - slot.get("attempted_at", -math.inf) >= retry:
        slot["attempted_at"] = now_seconds
        slot["future"] = _EXECUTOR.submit(function)


def _cancel(state):
    for slot in state.get("sources", {}).values():
        if slot.get("future") is not None:
            slot["future"].cancel()


def monitor_snapshot(state, region, bbox, start_date, end_date, provider, analysis_loader, now=None):
    now = now or datetime.now(timezone.utc)
    seconds = now.timestamp()
    target_key = (region, tuple(bbox))
    if state.get("target_key") != target_key:
        _cancel(state)
        state.clear()
        state.update({"target_key": target_key, "sources": {}, "cycle": 0, "history": []})
    query_key = (start_date, end_date, provider)
    if state.get("query_key") != query_key:
        old = state["sources"].get("satellite", {})
        if old.get("future") is not None:
            old["future"].cancel()
        state["sources"]["satellite"] = {}
        state["query_key"] = query_key
    location = GLOBAL_REGIONS.get(region, {})
    latitude = location.get("lat", (bbox[1] + bbox[3]) / 2)
    longitude = location.get("lon", (bbox[0] + bbox[2]) / 2)
    jobs = {
        "weather": (lambda: fetch_weather(latitude, longitude, int(seconds // WEATHER_POLL_SECONDS)), WEATHER_POLL_SECONDS),
        "river": (lambda: fetch_river(latitude, longitude, int(seconds // RIVER_POLL_SECONDS)), RIVER_POLL_SECONDS),
        "reports": (lambda: fetch_reports(latitude, longitude, region, int(seconds // REPORT_POLL_SECONDS)), REPORT_POLL_SECONDS),
        "satellite": (lambda: analysis_loader(tuple(bbox), start_date, end_date, int(seconds // 60)), 60),
    }
    for name, (function, interval) in jobs.items():
        _poll(state["sources"].setdefault(name, {}), function, interval, seconds)
    # Pick up tiny cached jobs immediately as well as on the next ten-second tick.
    for name, (function, interval) in jobs.items():
        _poll(state["sources"][name], function, interval, seconds)
    sources = state["sources"]
    weather, river, reports = (sources[name].get("data") for name in ("weather", "river", "reports"))
    usable_weather = weather
    if weather and abs((now - utc_time(weather["valid_at"])).total_seconds()) > 10800:
        usable_weather = None
    usable_river = river if river and river.get("valid_date") == now.date().isoformat() else None
    usable_reports = reports
    if reports and (now - utc_time(reports["fetched_at"])).total_seconds() > 3600:
        usable_reports = None
    numeric_finished = all(sources[name].get("completed") for name in ("weather", "river"))
    demo = numeric_finished and not usable_weather and not usable_river and not weather and not river and not (usable_reports or {}).get("nearby")
    signal = screen_conditions(usable_weather, usable_river, usable_reports)
    state["cycle"] += 1
    fingerprint = (weather.get("valid_at") if weather else None,
                   river.get("valid_date") if river else None,
                   river.get("discharge_m3s") if river else None)
    if demo:
        message = "DEMO only: real numerical feeds failed; synthetic preview is excluded from flood assessment."
    elif not weather and not river:
        message = "Querying real weather and river sources; the next check is in 10 seconds."
    elif fingerprint == state.get("fingerprint"):
        message = f"{signal['level']} · reassessed; no newer provider observation."
    else:
        message = f"{signal['level']} · source snapshot received and evaluated."
    state["fingerprint"] = fingerprint
    state["history"].append({"time": now.strftime("%H:%M:%S"), "message": message})
    state["history"] = state["history"][-4:]
    result = {
        "checked_at": now.isoformat(), "cycle": state["cycle"], "weather": weather,
        "river": river, "reports": reports, "signal": signal,
        "mode": "demo" if demo else ("live" if usable_weather or usable_river else ("stale" if weather or river else ("partial" if (usable_reports or {}).get("nearby") else "loading"))),
        "history": list(state["history"]), "coordinates": (latitude, longitude),
        "source_errors": {key: value["error"] for key, value in sources.items() if value.get("error")},
        "satellite": sources["satellite"].get("data"),
        "satellite_pending": sources["satellite"].get("future") is not None,
    }
    if demo:
        result["demo_preview"] = {
            "temperature_c": round(26 + 0.2 * math.sin(state["cycle"] / 3), 1),
            "rain_next24_mm": round(20 + 8 * math.sin(state["cycle"] / 4), 1),
        }
    return result
