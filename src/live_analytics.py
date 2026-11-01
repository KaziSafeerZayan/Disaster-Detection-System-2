"""Measured satellite/terrain summaries from public data, with optional Earth Engine.

Public radar is Sentinel-1 RTC gamma0 power, sampled on a fixed geographic grid.
It is not a flood classification. Copernicus DEM is a static surface reference.
"""
from datetime import date, datetime, timedelta, timezone
import math

import numpy as np
import rasterio
from rasterio.enums import Resampling
from rasterio.transform import from_bounds
from rasterio.warp import reproject, transform_bounds
from rasterio.windows import from_bounds as window_from_bounds
import requests
import streamlit as st


STAC_URL = "https://planetarycomputer.microsoft.com/api/stac/v1/search"
RADAR_GRID_SIZE = 192
REFRESH_SECONDS = 60
RASTER_ENV = {
    "GDAL_DISABLE_READDIR_ON_OPEN": "EMPTY_DIR",
    "GDAL_HTTP_TIMEOUT": 15,
    "GDAL_HTTP_MAX_RETRY": 1,
    "VSI_CACHE": True,
}


class DataSourceUnavailable(RuntimeError):
    pass


def validate_dates(start_date, end_date):
    start = date.fromisoformat(str(start_date))
    end = date.fromisoformat(str(end_date))
    if start > end:
        raise ValueError("Choose a SAR end date on or after the start date.")
    return start.isoformat(), end.isoformat()


def _json_request(url, params, label):
    try:
        response = requests.get(url, params=params, timeout=(5, 20))
        response.raise_for_status()
        return response.json()
    except (requests.RequestException, ValueError) as exc:
        raise DataSourceUnavailable(f"{label} is unavailable. Automatic retry in 60 seconds.") from exc


@st.cache_data(ttl=70, max_entries=64, show_spinner=False)
def public_scenes(bbox, start_date, end_date, refresh_bucket):
    """A date change queries immediately; periodic checks discover new acquisitions."""
    start, end = validate_dates(start_date, end_date)
    data = _json_request(STAC_URL, {
        "collections": "sentinel-1-rtc",
        "bbox": ",".join(map(str, bbox)),
        "datetime": f"{start}T00:00:00Z/{end}T23:59:59.999999Z",
        "sortby": "-datetime",
        "limit": 100,
    }, "Public satellite catalogue")
    items = [item for item in data.get("features", [])
             if "vv" in item.get("assets", {})
             and item.get("properties", {}).get("sar:instrument_mode") == "IW"]
    items.sort(key=lambda item: item["properties"]["datetime"], reverse=True)
    return {"items": items, "truncated": any(link.get("rel") == "next" for link in data.get("links", []))}


@st.cache_data(ttl=1800, max_entries=128, show_spinner=False)
def _signed_public_asset(href):
    # This endpoint currently issues temporary public read URLs without an account/key.
    return _json_request(
        "https://planetarycomputer.microsoft.com/api/sas/v1/sign", {"href": href},
        "Public satellite file access",
    )["href"]


@st.cache_data(ttl=86400, max_entries=128, show_spinner=False)
def _radar_grid(scene_id, href, bbox):
    """Read COG ranges, not the multi-gigabyte scene; align scenes on the same grid."""
    try:
        url = _signed_public_asset(href)
        with rasterio.Env(**RASTER_ENV), rasterio.open(url) as source:
            source_bounds = transform_bounds("EPSG:4326", source.crs, *bbox)
            window = window_from_bounds(*source_bounds, transform=source.transform).intersection(
                rasterio.windows.Window(0, 0, source.width, source.height)
            )
            sampled = source.read(1, window=window, out_shape=(RADAR_GRID_SIZE, RADAR_GRID_SIZE),
                                  masked=True, resampling=Resampling.average).astype("float64").filled(np.nan)
            sampled[sampled <= 0] = np.nan
            sampled_transform = source.window_transform(window) * rasterio.Affine.scale(
                window.width / RADAR_GRID_SIZE, window.height / RADAR_GRID_SIZE
            )
            values = np.full((RADAR_GRID_SIZE, RADAR_GRID_SIZE), np.nan)
            reproject(
                sampled, values, src_transform=sampled_transform, src_crs=source.crs,
                dst_transform=from_bounds(*bbox, RADAR_GRID_SIZE, RADAR_GRID_SIZE),
                dst_crs="EPSG:4326", src_nodata=np.nan, dst_nodata=np.nan,
                resampling=Resampling.average,
            )
        values[(values <= 0) | ~np.isfinite(values)] = np.nan
        return values
    except (rasterio.errors.RasterioError, KeyError) as exc:
        # Do not expose temporary signed URLs in the UI.
        raise DataSourceUnavailable("The satellite pixel file could not be read. Automatic retry in 60 seconds.") from exc


def power_statistics(values, bbox):
    valid = np.isfinite(values) & (values > 0)
    if not valid.any():
        raise DataSourceUnavailable("This satellite scene has no valid radar pixels in the selected area.")
    # Convert linear gamma0 power after averaging; do not treat raw power as dB.
    row_latitudes = bbox[3] - (np.arange(values.shape[0]) + 0.5) * (bbox[3] - bbox[1]) / values.shape[0]
    weights = np.broadcast_to(np.cos(np.deg2rad(row_latitudes))[:, None], values.shape)
    mean_power = np.average(values[valid], weights=weights[valid])
    return {
        "mean_db": float(10 * np.log10(mean_power)),
        "median_db": float(np.median(10 * np.log10(values[valid]))),
        "valid_cells": int(valid.sum()),
        "coverage_pct": float(valid.mean() * 100),
    }


def _same_orbit(first, second):
    a, b = first["properties"], second["properties"]
    keys = ("sat:relative_orbit", "sat:orbit_state")
    return all(a.get(key) is not None and a.get(key) == b.get(key) for key in keys)


def public_radar_summary(catalogue, bbox):
    items = catalogue["items"]
    if not items:
        return {"state": "empty", "message": "No published Sentinel-1 RTC observation intersects this area in the selected dates."}
    latest = items[0]
    values = _radar_grid(latest["id"], latest["assets"]["vv"]["href"], bbox)
    result = power_statistics(values, bbox)
    props = latest["properties"]
    result.update({
        "state": "ready", "source": "Sentinel-1 RTC / Microsoft Planetary Computer",
        "scene_id": latest["id"], "acquired_at": props["datetime"],
        "scene_count": len(items), "count_truncated": catalogue["truncated"],
        "orbit": props.get("sat:orbit_state", "unknown"),
        "relative_orbit": props.get("sat:relative_orbit"),
        "change_db": None, "baseline_at": None,
        "native_resolution_m": latest["assets"]["vv"].get("raster:bands", [{}])[0].get("spatial_resolution", 10),
        "grid_size": RADAR_GRID_SIZE,
        "sample_spacing_m": max(
            (bbox[2] - bbox[0]) * 111320 * math.cos(math.radians((bbox[1] + bbox[3]) / 2)),
            (bbox[3] - bbox[1]) * 111132,
        ) / RADAR_GRID_SIZE,
    })
    earlier = [item for item in items[1:] if _same_orbit(latest, item)
               and item["properties"]["datetime"] < props["datetime"]]
    if earlier:
        baseline = earlier[-1]
        try:
            reference = _radar_grid(baseline["id"], baseline["assets"]["vv"]["href"], bbox)
            common = np.isfinite(values) & np.isfinite(reference)
            if common.any():
                current_stats = power_statistics(np.where(common, values, np.nan), bbox)
                reference_stats = power_statistics(np.where(common, reference, np.nan), bbox)
                result["change_db"] = current_stats["mean_db"] - reference_stats["mean_db"]
                result["baseline_at"] = baseline["properties"]["datetime"]
        except DataSourceUnavailable:
            result["comparison_note"] = "Earlier same-orbit pixels are temporarily unavailable."
    return result


def _dem_url(latitude, longitude, resolution):
    northing = f"{'N' if latitude >= 0 else 'S'}{abs(latitude):02d}_00"
    easting = f"{'E' if longitude >= 0 else 'W'}{abs(longitude):03d}_00"
    arc_seconds = "10" if resolution == 30 else "30"
    tile = f"Copernicus_DSM_COG_{arc_seconds}_{northing}_{easting}_DEM"
    return f"https://copernicus-dem-{resolution}m.s3.amazonaws.com/{tile}/{tile}.tif"


@st.cache_data(ttl=86400, max_entries=64, show_spinner=False)
def public_terrain_summary(bbox):
    """Sample the real surface model. Elevation is not a live water-level reading."""
    heights, slopes, spacings, sources = [], [], [], []
    west, south, east, north = bbox
    missing_tiles = 0
    for latitude in range(math.floor(south), math.ceil(north)):
        for longitude in range(math.floor(west), math.ceil(east)):
            bounds = (max(west, longitude), max(south, latitude), min(east, longitude + 1), min(north, latitude + 1))
            loaded = False
            for resolution in (30, 90):
                try:
                    with rasterio.Env(**RASTER_ENV), rasterio.open(_dem_url(latitude, longitude, resolution)) as raster:
                        window = window_from_bounds(*bounds, transform=raster.transform)
                        height = min(1024, max(2, math.ceil(window.height)))
                        width = min(1024, max(2, math.ceil(window.width)))
                        data = raster.read(1, window=window, out_shape=(height, width),
                                           masked=True, resampling=Resampling.average).astype("float64").filled(np.nan)
                        transform = raster.window_transform(window) * rasterio.Affine.scale(window.width / width, window.height / height)
                    valid = np.isfinite(data)
                    if valid.any():
                        heights.append(data[valid])
                        center_latitude = (bounds[1] + bounds[3]) / 2
                        dx = abs(transform.a) * 111320 * math.cos(math.radians(center_latitude))
                        dy = abs(transform.e) * 111132
                        derivative_y, derivative_x = np.gradient(data)
                        slope = np.degrees(np.arctan(np.hypot(derivative_x / dx, derivative_y / dy)))
                        slopes.append(slope[np.isfinite(slope)])
                        spacings.append(max(dx, dy))
                        sources.append(resolution)
                    loaded = True
                    break
                except rasterio.errors.RasterioError as exc:
                    if "404" not in str(exc):
                        raise DataSourceUnavailable("Public terrain tiles are temporarily unavailable. Automatic retry in 60 seconds.") from exc
            if not loaded:
                missing_tiles += 1
    if not heights:
        raise DataSourceUnavailable("No public terrain tile covers this area.")
    elevation = np.concatenate(heights)
    slope = np.concatenate(slopes) if slopes else np.array([])
    return {
        "state": "ready", "source": "Copernicus DEM " + "/".join(f"GLO-{r}" for r in sorted(set(sources))),
        "median_elevation_m": float(np.median(elevation)),
        "min_elevation_m": float(elevation.min()), "max_elevation_m": float(elevation.max()),
        "mean_slope_deg": float(slope.mean()) if slope.size else None,
        "analysis_spacing_m": max(spacings), "missing_tiles": missing_tiles,
        "native_resolution_m": max(sources),
    }


def public_analysis(bbox, start_date, end_date, refresh_bucket, progress=None):
    """Independent source errors allow real terrain to remain usable if radar fails."""
    validate_dates(start_date, end_date)
    result = {"checked_at": datetime.now(timezone.utc).isoformat(), "provider": "public"}
    for name, operation in (
        ("terrain", lambda: public_terrain_summary(tuple(bbox))),
        ("radar", lambda: public_radar_summary(public_scenes(tuple(bbox), start_date, end_date, refresh_bucket), tuple(bbox))),
    ):
        if progress:
            progress(name, result)
        try:
            result[name] = operation()
        except (DataSourceUnavailable, requests.RequestException) as exc:
            result[name] = {"state": "unavailable", "message": str(exc)}
    return result


@st.cache_data(ttl=70, max_entries=64, show_spinner=False)
def _earth_engine_snapshot(bbox, start_date, end_date, project_id, credentials_version, refresh_bucket):
    import ee
    from src.gee_processor import sentinel1_collection

    roi, collection = sentinel1_collection(bbox, start_date, end_date)
    metadata = ee.Dictionary({
        "count": collection.size(),
        "latest": collection.aggregate_max("system:time_start"),
    }).getInfo()
    result = {"provider": "earth_engine", "checked_at": datetime.now(timezone.utc).isoformat()}
    try:
        result["terrain"] = _earth_engine_terrain(bbox, project_id, credentials_version)
    except Exception:
        result["terrain"] = {"state": "unavailable", "message": "Earth Engine terrain measurement failed; it will retry automatically."}
    if not metadata["count"]:
        result["radar"] = {"state": "empty", "message": "No descending IW/VV Sentinel-1 scenes were published for this area and date range."}
        return result
    latest = ee.Image(collection.sort("system:time_start", False).first())
    stats = latest.reduceRegion(
        reducer=ee.Reducer.mean().combine(ee.Reducer.count(), sharedInputs=True),
        geometry=roi, scale=30, maxPixels=5_000_000, tileScale=4,
    ).getInfo()
    if stats.get("VV_mean") is None:
        result["radar"] = {"state": "unavailable", "message": "No valid radar pixels cover this area in the latest scene."}
        return result
    # Coverage is measured from the mask on the same analysis grid, not assumed.
    mask_mean = latest.mask().unmask(0).reduceRegion(
        reducer=ee.Reducer.mean(), geometry=roi, scale=30, maxPixels=5_000_000, tileScale=4,
    ).getInfo().get("VV")
    result["radar"] = {
        "state": "ready", "source": "Sentinel-1 GRD / Google Earth Engine",
        "scene_count": metadata["count"],
        "acquired_at": datetime.fromtimestamp(metadata["latest"] / 1000, timezone.utc).isoformat(),
        "mean_db": stats["VV_mean"], "valid_cells": stats["VV_count"],
        "coverage_pct": (mask_mean or 0) * 100, "orbit": "descending",
        "relative_orbit": latest.get("relativeOrbitNumber_start").getInfo(),
        "native_resolution_m": 10, "sample_spacing_m": 30, "change_db": None,
        "comparison_note": "Latest observed radar summary; flood change classification is not applied.",
    }
    return result


@st.cache_data(ttl=86400, max_entries=64, show_spinner=False)
def _earth_engine_terrain(bbox, project_id, credentials_version):
    import ee
    elevation = ee.Image("USGS/SRTMGL1_003").select("elevation")
    slope = ee.Terrain.slope(elevation).rename("slope")
    stats = elevation.addBands(slope).reduceRegion(
        reducer=ee.Reducer.mean().combine(ee.Reducer.median(), sharedInputs=True),
        geometry=ee.Geometry.BBox(*bbox), scale=30, maxPixels=5_000_000, tileScale=4,
    ).getInfo()
    if stats.get("elevation_median") is None:
        raise DataSourceUnavailable("SRTM has no elevation coverage here.")
    return {"state": "ready", "source": "NASA/USGS SRTM",
            "median_elevation_m": stats["elevation_median"], "mean_slope_deg": stats.get("slope_mean"),
            "native_resolution_m": 30, "analysis_spacing_m": 30}


def earth_engine_analysis(bbox, start_date, end_date, refresh_bucket):
    import os
    from config import GEE_PROJECT_ID
    from src.gee_processor import initialize_gee, _credential_source

    validate_dates(start_date, end_date)
    initialize_gee()
    source, version, _ = _credential_source()
    return _earth_engine_snapshot(tuple(bbox), start_date, end_date,
                                  os.getenv("GEE_PROJECT_ID") or GEE_PROJECT_ID, (source, version), refresh_bucket)
