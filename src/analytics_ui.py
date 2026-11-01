"""The existing telemetry panel, driven by measurements and automatic checks."""
from datetime import datetime
from html import escape
from pathlib import Path
import subprocess
import sys

import streamlit as st

from src.live_analytics import public_analysis
from src.monitor_runtime import UI_REFRESH_SECONDS, monitor_snapshot


def _timestamp(value):
    if not value:
        return "unavailable"
    return datetime.fromisoformat(value.replace("Z", "+00:00")).strftime("%Y-%m-%d %H:%M:%S UTC")


def telemetry_html(region, start_date, end_date, snapshot=None, stage=None, error=None, stream=None):
    if stream is not None:
        return stream_telemetry_html(region, start_date, end_date, stream)
    snapshot = snapshot or {}
    lines = [
        ("TARGET", region),
        ("WINDOW", f"{start_date} to {end_date} · both dates included"),
    ]
    terrain, radar = snapshot.get("terrain", {}), snapshot.get("radar", {})
    if terrain.get("state") == "ready":
        slope = terrain.get("mean_slope_deg")
        slope_text = f"{slope:.2f}°" if slope is not None else "unavailable"
        lines.append(("TERRAIN", f"{terrain['source']} · median surface elevation {terrain['median_elevation_m']:.2f} m · mean derived slope {slope_text}"))
        lines.append(("DEM", f"{terrain['native_resolution_m']} m source · approximately {terrain['analysis_spacing_m']:.0f} m analysis spacing · static surface reference"))
        if terrain.get("missing_tiles"):
            lines.append(("COVERAGE", "Some terrain tiles are unavailable; summary covers available land tiles."))
    elif terrain.get("message"):
        lines.append(("TERRAIN", terrain["message"]))
    if radar.get("state") == "ready":
        suffix = "+" if radar.get("count_truncated") else ""
        lines.append(("RADAR", f"{radar['source']} · {radar['scene_count']}{suffix} observations in this range"))
        lines.append(("ACQUIRED", f"{_timestamp(radar['acquired_at'])} · {radar['orbit']} · relative orbit {radar.get('relative_orbit', 'unavailable')}"))
        coefficient = "γ⁰" if snapshot.get("provider") == "public" else "σ⁰"
        lines.append(("BACKSCATTER", f"Latest scene · sampled mean VV {coefficient}: {radar['mean_db']:.2f} dB · grid coverage {radar['coverage_pct']:.1f}%"))
        lines.append(("SAMPLING", f"{radar['native_resolution_m']} m source · approximately {radar['sample_spacing_m']:.0f} m analysis grid · {radar['valid_cells']:,} valid cells"))
        if radar.get("change_db") is not None:
            lines.append(("CHANGE", f"{radar['change_db']:+.2f} dB versus {_timestamp(radar['baseline_at'])} · same orbit and common valid cells"))
        else:
            lines.append(("CHANGE", radar.get("comparison_note", "No earlier comparable same-orbit observation in this range.")))
    elif radar.get("message"):
        lines.append(("RADAR", radar["message"]))
    state = "loading" if stage else ("unavailable" if error else "ready")
    if stage:
        lines.append(("STATUS", f"Reading {stage} measurements…"))
    elif error:
        lines.append(("STATUS", error))
    else:
        states = [item.get("state") for item in (terrain, radar)]
        state = "ready" if states == ["ready", "ready"] else "partial"
        lines.append(("STATUS", "Measurements ready." if state == "ready" else "Some measurements are unavailable; available source results are shown above."))
    if snapshot.get("checked_at") and not stage:
        lines.append(("CHECKED", _timestamp(snapshot["checked_at"])))
    lines.append(("MONITOR", "Automatically checks every 60 s while this page is open. New values depend on published satellite observations."))
    content = "".join(f'<div class="telemetry-line"><span class="telemetry-tag">[{escape(tag)}]</span> {escape(value)}</div>' for tag, value in lines)
    return f'<div class="telemetry-log telemetry-log--live" data-state="{state}" aria-live="polite" aria-atomic="true">{content}</div>'


def _display(value, unit="", digits=1):
    return f"{value:.{digits}f}{unit}" if value is not None else "unavailable"


def stream_telemetry_html(region, start_date, end_date, stream):
    lines = [("10S CHECK", f"#{stream['cycle']} · {_timestamp(stream['checked_at'])} · next check in 10 seconds"),
             ("TARGET", f"{region} · point forecast near {stream['coordinates'][0]:.3f}, {stream['coordinates'][1]:.3f}; not division-wide coverage")]
    mode = stream["mode"]
    signal = stream["signal"]
    if mode == "demo":
        preview = stream["demo_preview"]
        lines.extend([
            ("MODE", "DEMO · SYNTHETIC VALUES. Real weather and river feeds failed. Excluded from flood assessment."),
            ("DEMO ONLY", f"Synthetic temperature {preview['temperature_c']:.1f}°C · synthetic 24h rain {preview['rain_next24_mm']:.1f} mm"),
        ])
    elif mode == "loading":
        lines.append(("MODE", "Contacting real weather, river and report sources in the background…"))
    elif mode == "stale":
        lines.append(("MODE", "Last-known readings are stale; they are excluded from the current screening signal."))
    elif mode == "partial":
        lines.append(("MODE", "Published event context is available; numerical weather and river inputs are unavailable."))
    else:
        lines.append(("MODE", "REAL SOURCE DATA · weather estimates and forecasts; not live gauge measurements"))
    lines.append(("SIGNAL", signal["level"]))
    lines.append(("WHY", signal["reason"]))
    weather = stream.get("weather")
    if weather:
        interval = int(weather.get("rain_interval_seconds", 900) / 60)
        lines.extend([
            ("WEATHER", f"{_display(weather.get('temperature_c'), '°C')} · humidity {_display(weather.get('humidity_pct'), '%', 0)} · rain {_display(weather.get('rain_current_mm'), ' mm')} / {interval} min"),
            ("RAINFALL", f"Past 24h model total {_display(weather.get('rain_past24_mm'), ' mm')} · next 24h forecast {_display(weather.get('rain_next24_mm'), ' mm')} · max rain chance {_display(weather.get('max_rain_probability_pct'), '%', 0)}"),
            ("WX SOURCE", f"{weather['source']} · valid {_timestamp(weather['valid_at'])} · near-surface soil moisture {_display(weather.get('soil_moisture'), ' m³/m³', 3)}"),
        ])
    river = stream.get("river")
    if river:
        change = river.get("change_next3_pct")
        change_text = f"{change:+.1f}%" if change is not None else "unavailable"
        lines.append(("RIVER MODEL", f"GloFAS · {river['valid_date']} · {_display(river.get('discharge_m3s'), ' m³/s')} · next 3-day peak {_display(river.get('peak_next3_m3s'), ' m³/s')} ({change_text}) · not a water-level gauge"))
    reports = stream.get("reports")
    if reports:
        lines.append(("SEARCH", f"GDACS · {reports['examined']} flood reports inspected · {len(reports['nearby'])} recent matches within 100 km. No matches does not mean no flooding."))
        for report in reports["nearby"][:1]:
            lines.append(("REPORT", f"{report['alert_level']} · {report['title']} · {report['distance_km']:.0f} km away"))
    for entry in stream.get("history", [])[-2:]:
        lines.append((entry["time"], entry["message"]))
    satellite = stream.get("satellite") or {}
    terrain, radar = satellite.get("terrain", {}), satellite.get("radar", {})
    lines.append(("SAR WINDOW", f"{start_date} to {end_date} · weather above follows current conditions"))
    if terrain.get("state") == "ready":
        lines.append(("TERRAIN", f"{terrain['source']} · median {_display(terrain['median_elevation_m'], ' m', 2)} · derived slope {_display(terrain.get('mean_slope_deg'), '°', 2)} · static surface reference"))
    if radar.get("state") == "ready":
        coefficient = "γ⁰" if satellite.get("provider") == "public" else "σ⁰"
        lines.append(("SAR", f"VV {coefficient} {radar['mean_db']:.2f} dB · acquired {_timestamp(radar['acquired_at'])} · {radar['coverage_pct']:.1f}% sampled grid coverage"))
    elif radar.get("message"):
        lines.append(("SAR", radar["message"]))
    elif stream.get("satellite_pending") and not satellite:
        lines.append(("SAR", "Satellite and terrain analysis is running separately; the 10-second weather stream continues."))
    for source, message in stream.get("source_errors", {}).items():
        lines.append((source.upper(), f"Source retry pending: {message}"))
    lines.append(("PROTOTYPE", "Interpretable screening rules, not a calibrated flood probability. Text vectors retrieve reports; they do not determine flood risk."))
    body = "".join(f'<div class="telemetry-line"><span class="telemetry-tag">[{escape(tag)}]</span> {escape(value)}</div>' for tag, value in lines)
    return f'<div class="telemetry-log telemetry-log--live telemetry-log--stream" data-state="{mode}" aria-live="polite" aria-atomic="true">{body}</div>'


@st.fragment(run_every=f"{UI_REFRESH_SECONDS}s", parallel=True)
def render_live_analysis(region, bbox, start_date, end_date, provider):
    slot = st.empty()
    try:
        state = st.session_state.setdefault("live_monitor_state", {})
        if provider == "earth_engine":
            from src.live_analytics import earth_engine_analysis
            loader = earth_engine_analysis
        else:
            loader = public_analysis
        stream = monitor_snapshot(state, region, bbox, start_date, end_date, provider, loader)
        slot.markdown(telemetry_html(region, start_date, end_date, stream=stream), unsafe_allow_html=True)
    except Exception as exc:
        slot.markdown(telemetry_html(region, start_date, end_date, error=str(exc)), unsafe_allow_html=True)


def render_data_connection():
    with st.popover("Data sources & sign-in"):
        selected = st.radio("Satellite analytics source", ["Public data · no sign-in", "Google Earth Engine"], key="analytics_source")
        st.caption("Weather, river and report monitoring uses public feeds with either satellite-source choice.")
        st.caption("Public mode reads Sentinel-1 RTC satellite pixels and Copernicus elevation tiles without an account or API key.")
        st.caption("Sources: [Sentinel-1 RTC](https://planetarycomputer.microsoft.com/dataset/sentinel-1-rtc) · [Copernicus DEM](https://registry.opendata.aws/copernicus-dem/). Terrain summaries cover the selected map preset's bounding box.")
        st.caption("10-second monitoring: [Open-Meteo weather](https://open-meteo.com/en/docs), [GloFAS river forecasts](https://open-meteo.com/en/docs/flood-api), [GDACS reports](https://www.gdacs.org/) and [MET Norway](https://api.met.no/weatherapi/locationforecast/2.0/documentation) as a weather backup. Models publish slower than the check interval. Synthetic fallback, if ever needed, is labelled DEMO and excluded from flood assessment.")
        st.caption("Earth Engine is optional and requires an authorized Google Cloud project. Your Google sign-in opens in your default browser.")
        login_process = st.session_state.get("earth_engine_login_process")
        login_pending = login_process is not None and login_process.poll() is None
        if login_pending:
            st.caption("Google sign-in is waiting for completion in your browser.")
        if st.button("Sign in to Google Earth Engine", key="earth_engine_sign_in", disabled=login_pending):
            root = Path(__file__).resolve().parent.parent
            (root / "logs").mkdir(exist_ok=True)
            with (root / "logs" / "earth-engine-sign-in.log").open("a", encoding="utf-8") as log:
                process = subprocess.Popen(
                    [sys.executable, str(root / "authenticate_gee.py")], cwd=root,
                    stdin=subprocess.DEVNULL, stdout=log, stderr=log,
                    creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
                )
            st.session_state["earth_engine_login_process"] = process
            st.info("Complete Google sign-in in your browser, then select Google Earth Engine above. The public source remains available.")
    return "earth_engine" if selected == "Google Earth Engine" else "public"
