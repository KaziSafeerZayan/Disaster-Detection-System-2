"""
Google Earth Engine Processor for Global Sentinel-1 SAR Imagery & Satellite Tiles.
"""
import ee
import folium
from config import GEE_PROJECT_ID
import streamlit as st

def initialize_gee(project_id: str = None):
    """Initializes Google Earth Engine API with a Google Cloud Project ID."""
    p_id = project_id or GEE_PROJECT_ID
    try:
        if p_id and p_id != "your-google-cloud-project-id":
            ee.Initialize(project=p_id)
        else:
            ee.Initialize()
    except Exception as e:
        print(f"Authentication required: {e}")
        ee.Authenticate()
        if p_id and p_id != "your-google-cloud-project-id":
            ee.Initialize(project=p_id)
        else:
            ee.Initialize()

@st.cache_data(show_spinner=False)
def get_global_sentinel1_sar(geometry_bbox, start_date, end_date):
    """Retrieves global Sentinel-1 SAR GRD VV backscatter median composite."""
    roi = ee.Geometry.BBox(*geometry_bbox)

    collection = (
        ee.ImageCollection("COPERNICUS/S1_GRD")
        .filterBounds(roi)
        .filterDate(start_date, end_date)
        .filter(ee.Filter.eq('instrumentMode', 'IW'))
        .filter(ee.Filter.listContains('transmitterReceiverPolarization', 'VV'))
        .filter(ee.Filter.eq('orbitProperties_pass', 'DESCENDING'))
        .select('VV')
    )

    sar_mosaic = collection.median().clip(roi)
    return sar_mosaic

def add_esri_satellite_layer(map_obj):
    """Adds high-resolution Esri World Imagery satellite base layer (No token required)."""
    folium.raster_layers.TileLayer(
        tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
        attr='Esri &mdash; Source: Esri, i-cubed, USDA, USGS, AEX, GeoEye, Getmapping, Aerogrid, IGN, IGP, UPR-EGP, and the GIS User Community',
        name='Esri Satellite',
        overlay=False,
        control=True
    ).add_to(map_obj)

def add_ee_layer(self, ee_image_object, vis_params, name):
    """Adds Earth Engine image tiles to folium map."""
    map_id_dict = ee.Image(ee_image_object).getMapId(vis_params)
    folium.raster_layers.TileLayer(
        tiles=map_id_dict['tile_fetcher'].url_format,
        attr='Map Data © Google Earth Engine',
        name=name,
        overlay=True,
        control=True
    ).add_to(self)

folium.Map.add_ee_layer = add_ee_layer
get_sentinel1_sar_layer = get_global_sentinel1_sar
