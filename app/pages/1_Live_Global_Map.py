"""
Live Global Satellite Map with Top Navigation, Smart Search, and Sentinel-1 SAR Radar.
"""
import streamlit as st
import folium
from streamlit_folium import st_folium
from datetime import datetime, timedelta
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from config import GLOBAL_REGIONS
from src.design_system import apply_design_system, style_satellite_map, map_marker
from src.gee_processor import add_sentinel1_layer, add_esri_satellite_layer, add_waterways_layer
from src.geocoder_service import GlobalGeocoder

st.set_page_config(page_title="Satellite Assisted Flood Detection System | Satellite Map", page_icon=":material/radar:", layout="wide")

apply_design_system()

#  Clean Top Navigation Bar
st.markdown("### Navigation Menu")
nav1, nav2 = st.columns(2)
with nav1:
    if st.button("Live Global Map", use_container_width=True, type="primary"):
        st.switch_page("pages/1_Live_Global_Map.py")
with nav2:
    if st.button("Risk Analytics & Exposure", use_container_width=True):
        st.switch_page("pages/2_Risk_Analytics.py")

st.markdown("---")
st.header("Live Satellite Global Map & Smart Search")

geocoder = GlobalGeocoder()

if "selected_region_name" not in st.session_state:
    st.session_state["selected_region_name"] = "Khulna Sadar, Bangladesh"

# Main Layout Controls (Moved out of sidebar into clean columns)
col_ctrl1, col_ctrl2, col_ctrl3, col_ctrl4 = st.columns([2, 2, 1, 1])

with col_ctrl1:
    preset_options = ["Custom Search..."] + list(GLOBAL_REGIONS.keys())
    default_index = preset_options.index(st.session_state["selected_region_name"]) if st.session_state["selected_region_name"] in preset_options else 0
    preset_location = st.selectbox("Preset Regions", preset_options, index=default_index)

with col_ctrl2:
    search_query = st.text_input("Smart Search (Type any place worldwide)", "")

with col_ctrl3:
    start_date = st.date_input("Start Date", datetime.now() - timedelta(days=10))

with col_ctrl4:
    end_date = st.date_input("End Date", datetime.now())

# Determine active location metadata
active_lat, active_lon, active_zoom, active_bbox = 22.8456, 89.5403, 12, [89.48, 22.78, 89.62, 22.92]
active_name = "Khulna Sadar, Bangladesh"

if preset_location != "Custom Search...":
    active_name = preset_location
    reg = GLOBAL_REGIONS[preset_location]
    active_lat, active_lon, active_zoom, active_bbox = reg["lat"], reg["lon"], reg["zoom"], reg["bbox"]
elif search_query:
    result = geocoder.search_place(search_query)
    if result:
        active_name = search_query
        active_lat, active_lon, active_bbox = result["lat"], result["lon"], result["bbox"]
        st.success(f"Found: {result['name']}")

st.session_state["selected_region_name"] = active_name

# Initialize Folium Map with Esri Satellite Layer
m = folium.Map(location=[active_lat, active_lon], zoom_start=active_zoom, tiles=None)
add_esri_satellite_layer(m)
style_satellite_map(m)

# Radar is optional; mapped waterways remain visible without Google sign-in.
try:
    add_sentinel1_layer(
        m,
        geometry_bbox=active_bbox,
        start_date=start_date.strftime("%Y-%m-%d"),
        end_date=end_date.strftime("%Y-%m-%d")
    )
except Exception as e:
    st.caption(str(e))

add_waterways_layer(m)

# Add Color-Coded Risk Markers
for reg_name, data in GLOBAL_REGIONS.items():
    pop = data.get("pop", 50000)
    if pop > 1000000:
        color, risk_text = "red", "HIGH RISK"
    elif pop > 400000:
        color, risk_text = "orange", "MODERATE RISK"
    else:
        color, risk_text = "green", "LOW RISK"

    popup_html = f"""
    <div style="font-family: sans-serif; width: 200px;">
        <h4 style="margin:0; color: #333;">{reg_name}</h4>
        <p style="margin: 5px 0;"><b>Risk Level:</b> <span class="map-status--{color}">{risk_text}</span></p>
        <p style="margin: 0;"><b>Population:</b> {pop:,}</p>
    </div>
    """
    folium.Marker(
        location=[data["lat"], data["lon"]],
        popup=folium.Popup(popup_html, max_width=250),
        tooltip=f"{reg_name} ({risk_text})",
        icon=map_marker({"red": "critical", "orange": "warning", "green": "success"}[color])
    ).add_to(m)

folium.LayerControl().add_to(m)
st_folium(m, use_container_width=True, height=520)

st.info("**Tip:** Click any pin on the map to target an area, then click the **Risk Analytics** button at the top to review its vulnerability profile.")
