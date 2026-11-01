"""Satellite imagery, mapped waterways, and optional Earth Engine radar access."""
import os
from datetime import date, timedelta
from pathlib import Path

import ee
import folium
from folium.plugins import VectorGridProtobuf
import httplib2
import streamlit as st

from config import GEE_PROJECT_ID


class EarthEngineUnavailable(RuntimeError):
    """An actionable connection error that the dashboard can display."""


def _credential_source():
    """Avoid Google's slow metadata-server lookup on an unauthenticated desktop."""
    application_credentials = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    path = Path(application_credentials) if application_credentials else Path(ee.oauth.get_credentials_path())
    if not path.is_file():
        raise EarthEngineUnavailable(
            "Radar is unavailable: Google Earth Engine sign-in is required. "
            "Run authenticate.bat in the project folder, then reload the site. "
            "Mapped waterways remain available."
        )
    return str(path), path.stat().st_mtime_ns, bool(application_credentials)


@st.cache_resource(ttl=300, show_spinner=False)
def _initialize_gee_cached(project_id, credential_path, credential_version, application_credentials):
    """Cache both a connection and its error; a new login invalidates the cache."""
    try:
        credentials = "persistent"
        if application_credentials:
            import google.auth

            credentials, _ = google.auth.load_credentials_from_file(
                credential_path, scopes=ee.oauth.SCOPES
            )
        ee.Initialize(
            credentials=credentials,
            project=project_id,
            http_transport=httplib2.Http(timeout=15),
        )
    except Exception as exc:
        return (
            f"Radar could not connect to Earth Engine project '{project_id}': {exc}. "
            "Run authenticate.bat and confirm that your account has access to an "
            "Earth Engine-enabled Google Cloud project. Mapped waterways remain available."
        )
    return None


def initialize_gee(project_id=None):
    """Connect without opening a login prompt inside a dashboard rerun."""
    project_id = project_id or os.getenv("GEE_PROJECT_ID") or GEE_PROJECT_ID
    source, version, application_credentials = _credential_source()
    error = _initialize_gee_cached(project_id, source, version, application_credentials)
    if error:
        raise EarthEngineUnavailable(error)


@st.cache_resource(ttl=1800, show_spinner=False)
def get_global_sentinel1_sar(geometry_bbox, start_date, end_date):
    """Retrieve the existing Sentinel-1 VV backscatter median composite."""
    roi, collection = sentinel1_collection(geometry_bbox, start_date, end_date)
    return collection.median().clip(roi)


def sentinel1_collection(geometry_bbox, start_date, end_date):
    start, end = date.fromisoformat(start_date), date.fromisoformat(end_date)
    if start > end:
        raise ValueError("Choose a SAR end date on or after the start date.")
    roi = ee.Geometry.BBox(*geometry_bbox)
    collection = (
        ee.ImageCollection("COPERNICUS/S1_GRD")
        .filterBounds(roi)
        .filterDate(start.isoformat(), (end + timedelta(days=1)).isoformat())
        .filter(ee.Filter.eq("instrumentMode", "IW"))
        .filter(ee.Filter.eq("resolution_meters", 10))
        .filter(ee.Filter.listContains("transmitterReceiverPolarisation", "VV"))
        .filter(ee.Filter.eq("orbitProperties_pass", "DESCENDING"))
        .select("VV")
    )
    return roi, collection


@st.cache_data(ttl=1800, show_spinner=False)
def _radar_tile_url(geometry_bbox, start_date, end_date, project_id, credential_version):
    image = get_global_sentinel1_sar(geometry_bbox, start_date, end_date)
    vis = {"min": -25.0, "max": -5.0, "palette": ["000080", "0000ff", "00ffff", "ffffff"]}
    return ee.Image(image).getMapId(vis)["tile_fetcher"].url_format


def add_sentinel1_layer(map_obj, geometry_bbox, start_date, end_date):
    """Reuse radar tile URLs rather than requesting a new map on every rerun."""
    project_id = os.getenv("GEE_PROJECT_ID") or GEE_PROJECT_ID
    initialize_gee(project_id)
    source, version, _ = _credential_source()
    url = _radar_tile_url(tuple(geometry_bbox), start_date, end_date, project_id, (source, version))
    folium.TileLayer(
        tiles=url,
        attr="Map Data © Google Earth Engine",
        name="Sentinel-1 SAR Flood Extent",
        overlay=True,
        control=True,
    ).add_to(map_obj)


def add_esri_satellite_layer(map_obj):
    """Selectable public basemaps; display filters never alter analytical overlays."""
    folium.map.CustomPane("satellite", z_index=200).add_to(map_obj)
    root = "https://server.arcgisonline.com/ArcGIS/rest/services/"
    cartography = ('Tiles &copy; Esri, HERE, Garmin, '
                   '<a href="https://www.openstreetmap.org/copyright">&copy; OpenStreetMap</a> '
                   'contributors, and the GIS user community')
    basemaps = (
        ("Satellite imagery", "World_Imagery", "Tiles &copy; Esri, Vantor, Earthstar Geographics, and the GIS User Community"),
        ("Dark atlas", "Canvas/World_Dark_Gray_Base", cartography),
        ("Light atlas", "Canvas/World_Light_Gray_Base", cartography),
        ("Topographic", "World_Topo_Map", "Tiles &copy; Esri, HERE, Garmin, Intermap, increment P Corp., GEBCO, USGS, FAO, NPS, NRCAN, GeoBase, IGN, Kadaster NL, Ordnance Survey, Esri Japan, METI, Esri China (Hong Kong), OpenStreetMap contributors, and the GIS User Community"),
    )
    for index, (name, service, attribution) in enumerate(basemaps):
        folium.TileLayer(
            tiles=f"{root}{service}/MapServer/tile/{{z}}/{{y}}/{{x}}",
            attr=attribution, name=name, pane="satellite", overlay=False,
            control=True, show=index == 0, max_zoom=22, max_native_zoom=19,
        ).add_to(map_obj)
    folium.map.CustomPane("map-labels", z_index=460, pointer_events=False).add_to(map_obj)
    folium.TileLayer(
        tiles=f"{root}Reference/World_Boundaries_and_Places/MapServer/tile/{{z}}/{{y}}/{{x}}",
        attr=cartography, name="Place labels & borders", pane="map-labels",
        overlay=True, control=True, show=False, max_zoom=22, max_native_zoom=19,
    ).add_to(map_obj)


def add_waterways_layer(map_obj):
    """Highlight mapped rivers, canals, streams, and lakes independently of radar."""
    folium.map.CustomPane("waterways", z_index=450).add_to(map_obj)
    # OpenMapTiles contains other feature classes, which must be explicitly hidden.
    options = """{
        pane: 'waterways',
        rendererFactory: L.canvas.tile,
        interactive: false,
        maxNativeZoom: 14,
        maxZoom: 22,
        attribution: '<a href="https://openfreemap.org">OpenFreeMap</a> · <a href="https://openmaptiles.org">© OpenMapTiles</a> · <a href="https://www.openstreetmap.org/copyright">© OpenStreetMap</a>',
        vectorTileLayerStyles: {
            aerodrome_label: [], aeroway: [], boundary: [], building: [],
            housenumber: [], landcover: [], landuse: [], mountain_peak: [],
            park: [], place: [], poi: [], transportation: [], transportation_name: [],
            water_name: [],
            water: function(properties) {
                if (properties.class === 'ocean') return [];
                return {
                    fill: true, fillColor: '#49cce3', fillOpacity: 0.42,
                    color: '#8ae8f2', opacity: 0.75, weight: 0.65
                };
            },
            waterway: function(properties, zoom) {
                if (properties.brunnel === 'tunnel') return [];
                return {
                    color: '#8ae8f2', opacity: 0.95,
                    weight: properties.class === 'river' ? Math.max(1.4, Math.min(3.2, (zoom - 5) * 0.3)) : 1.25
                };
            }
        }
    }"""
    layer = VectorGridProtobuf(
        "https://tiles.openfreemap.org/planet/latest/{z}/{x}/{y}.pbf",
        name="Waterways · rivers & lakes (mapped)",
        options=options,
        show=True,
    )
    # Pin the renderer version rather than loading an unbounded @latest build.
    layer.default_js = [("vectorGrid", "https://unpkg.com/leaflet.vectorgrid@1.3.0/dist/Leaflet.VectorGrid.bundled.js")]
    layer.add_to(map_obj)
    return layer


def add_ee_layer(self, ee_image_object, vis_params, name):
    """Compatibility helper for existing Earth Engine callers."""
    map_id_dict = ee.Image(ee_image_object).getMapId(vis_params)
    folium.TileLayer(
        tiles=map_id_dict["tile_fetcher"].url_format,
        attr="Map Data © Google Earth Engine",
        name=name,
        overlay=True,
        control=True,
    ).add_to(self)


folium.Map.add_ee_layer = add_ee_layer
get_sentinel1_sar_layer = get_global_sentinel1_sar
