"""
Satellite Assisted Flood Detection System
Single-Page App with High-Tech Command Center Styling, Live Telemetry Stream,
Flood and waterlogging risk, Map Click-to-Sync, and Scenario Simulators.
"""
import streamlit as st
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.design_system import (apply_design_system, render_phase_navigation, phase_heading,
                               status_message, style_satellite_map, map_marker, style_chart)

st.set_page_config(
    page_title="Satellite Assisted Flood Detection System",
    page_icon=":material/radar:",
    layout="wide",
    initial_sidebar_state="collapsed"
)

apply_design_system()
render_phase_navigation()

# App Header with High-Tech Badges
st.title("Satellite Assisted Flood Detection System")
st.markdown("""
    <div class="status-strip">
        <span class="tech-badge">GEE PIPELINE: ACTIVE</span>
        <span class="tech-badge">SENTINEL-1 SAR: SYNCED</span>
        <span class="tech-badge">DEM ELEVATION GRID: OPTIMIZED</span>
        <span class="tech-badge">ANTI-DEADLOCK: SECURE</span>
    </div>
""", unsafe_allow_html=True)

import folium
from streamlit_folium import st_folium
from datetime import datetime, timedelta
import pandas as pd
import plotly.express as px

from config import GLOBAL_REGIONS
from src.gee_processor import add_sentinel1_layer, add_esri_satellite_layer, add_waterways_layer
from src.analytics_ui import render_live_analysis, render_data_connection

if "selected_region_name" not in st.session_state:
    st.session_state["selected_region_name"] = "Khulna Division, Bangladesh"

# ==========================================
#  GLOBAL LOCATION COMMAND CENTER BAR
# ==========================================
st.markdown("### Global Location Command Center")
col_g1, col_g2 = st.columns([3, 1])

with col_g1:
    regions_list = list(GLOBAL_REGIONS.keys())
    current_index = regions_list.index(st.session_state["selected_region_name"]) if st.session_state["selected_region_name"] in regions_list else 0

    def update_global_region():
        st.session_state["selected_region_name"] = st.session_state["global_region_selectbox"]

    selected_region = st.selectbox(
        "Select Active Global Region / Target Zone",
        regions_list,
        index=current_index,
        key="global_region_selectbox",
        on_change=update_global_region
    )
    st.session_state["selected_region_name"] = selected_region

with col_g2:
    st.info(f"Target: **{st.session_state['selected_region_name']}**")

st.markdown("---")

active_reg_data = GLOBAL_REGIONS.get(st.session_state["selected_region_name"], {"lat": 22.8456, "lon": 89.5403, "zoom": 10, "bbox": [89.40, 22.70, 89.70, 22.95], "pop": 17000000})
active_lat = active_reg_data["lat"]
active_lon = active_reg_data["lon"]
active_zoom = active_reg_data["zoom"]
active_bbox = active_reg_data["bbox"]
base_pop = active_reg_data.get("pop", 17000000)

topo_profile = {
    "Dhaka Division, Bangladesh": {"elevation": 6.5, "slope": 0.8},
    "Chattogram Division, Bangladesh": {"elevation": 18.0, "slope": 3.5},
    "Rajshahi Division, Bangladesh": {"elevation": 19.2, "slope": 1.5},
    "Khulna Division, Bangladesh": {"elevation": 3.2, "slope": 0.4},
    "Sylhet Division, Bangladesh": {"elevation": 14.0, "slope": 1.2},
    "Barishal Division, Bangladesh": {"elevation": 1.8, "slope": 0.2},
    "Rangpur Division, Bangladesh": {"elevation": 32.0, "slope": 2.1},
    "Mymensingh Division, Bangladesh": {"elevation": 12.0, "slope": 1.0},
    "Venice, Italy": {"elevation": 1.0, "slope": 0.1},
    "Amsterdam, Netherlands": {"elevation": -2.0, "slope": 0.05},
    "Tokyo, Japan": {"elevation": 12.5, "slope": 4.1},
    "San Francisco, USA": {"elevation": 16.0, "slope": 8.5},
    "Istanbul, Turkey": {"elevation": 35.0, "slope": 5.2},
    "Santiago, Chile": {"elevation": 570.0, "slope": 6.8},
    "Wellington, New Zealand": {"elevation": 20.0, "slope": 7.5}
}
current_topo = topo_profile.get(st.session_state["selected_region_name"], {"elevation": 8.0, "slope": 2.0})

# ==========================================
# PHASE 1: SATELLITE RADAR & FLOOD MAP
# ==========================================
with st.container(key="phase-1"):
    phase_heading(1, "Satellite Radar & Flood Map")

    col_date1, col_date2 = st.columns(2)
    with col_date1:
        start_date = st.date_input("SAR Data Start Date", datetime.now() - timedelta(days=10))
    with col_date2:
        end_date = st.date_input("SAR Data End Date", datetime.now())

    analytics_provider = render_data_connection()

    m = folium.Map(location=[active_lat, active_lon], zoom_start=active_zoom, tiles=None)
    add_esri_satellite_layer(m)
    style_satellite_map(m)

    if analytics_provider == "earth_engine":
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

    for reg_name, data in GLOBAL_REGIONS.items():
        t_data = topo_profile.get(reg_name, {"elevation": 8.0, "slope": 2.0})
        is_high_hazard = t_data["elevation"] < 5.0
        is_mod_hazard = t_data["elevation"] < 15.0

        color, hazard_lbl = ("red", "HIGH HAZARD") if is_high_hazard else (("orange", "MODERATE HAZARD") if is_mod_hazard else ("green", "STABLE"))

        popup_html = f"""
        <div style="font-family: sans-serif; width: 190px;">
            <h4 style="margin:0; color: #1e293b;">{reg_name}</h4>
            <p style="margin: 4px 0;"><b>Status:</b> <span class="map-status--{color}">{hazard_lbl}</span></p>
            <p style="margin: 0; font-size: 11px;">Elev: {t_data['elevation']}m | Slope: {t_data['slope']}°</p>
        </div>
        """
        folium.Marker(
            location=[data["lat"], data["lon"]],
            popup=folium.Popup(popup_html, max_width=220),
            tooltip=f"{reg_name} ({hazard_lbl})",
            icon=map_marker({"red": "critical", "orange": "warning", "green": "success"}[color])
        ).add_to(m)

    folium.LayerControl().add_to(m)

    map_output = st_folium(
        m,
        use_container_width=True,
        height=500,
        key="multi_hazard_map",
        returned_objects=["last_clicked"]
    )

    if map_output and map_output.get("last_clicked"):
        click_data = map_output["last_clicked"]
        c_lat = click_data.get("lat")
        c_lon = click_data.get("lng")

        if c_lat is not None and c_lon is not None:
            closest_reg = None
            min_dist = float("inf")
            for r_name, r_info in GLOBAL_REGIONS.items():
                dist = ((r_info["lat"] - c_lat) ** 2 + (r_info["lon"] - c_lon) ** 2) ** 0.5
                if dist < min_dist:
                    min_dist = dist
                    closest_reg = r_name

            if closest_reg and min_dist < 1.5:
                if st.session_state.get("selected_region_name") != closest_reg:
                    st.session_state["selected_region_name"] = closest_reg
                    st.rerun()


@st.fragment
def render_scenario(current_topo, base_pop, region, bbox, start_date, end_date, provider):
    """Update the existing scenario and protocol without rerunning the map."""
    # ==========================================
    # PHASE 2: FLOOD & TERRAIN ANALYTICS + SIMULATOR
    # ==========================================
    with st.container(key="phase-2"):
        phase_heading(2, "Flood & Terrain Analytics", st.session_state["selected_region_name"])

        render_live_analysis(region, bbox, start_date, end_date, provider)
        st.caption("Weather and river screening follows current conditions near the target point; SAR observations use the selected dates. The scenario below retains its preset elevation, exposure percentages, and simulated chart.")

        st.markdown("#### Live Predictive Scenario Simulator")
        simulated_water_rise = st.slider("Simulated Water Level Rise (m)", 0.0, 5.0, 0.0, 0.5)

        st.markdown("---")

        base_elevation = current_topo["elevation"]
        effective_elevation = max(0.0, base_elevation - simulated_water_rise)
        slope = current_topo["slope"]

        if effective_elevation < 3.0 and slope < 0.8:
            flood_status = "CRITICAL INUNDATION: Severe Hydro-Flooding Under Simulation!"
        elif effective_elevation < 8.0:
            flood_status = "ELEVATED RISK: Moderate Waterlogging & Runoff Stress"
        else:
            flood_status = "STABLE: Low Vulnerability to Current Simulated Rise"

        st.subheader("Floods & Waterlogging")
        status_message(flood_status, "critical" if effective_elevation < 3.0 and slope < 0.8 else ("warning" if effective_elevation < 8.0 else "success"))
        elevation_column, slope_column = st.columns(2)
        with elevation_column:
            st.metric("Effective Elevation (Simulated)", f"{effective_elevation:.1f} meters", f"Base: {base_elevation}m (-{simulated_water_rise}m)")
        with slope_column:
            st.metric("Basin Drainage Slope", f"{slope}°", "Surface Runoff Gradient")
        flood_exposed_pop = int(base_pop * (0.35 if effective_elevation < 3.0 else (0.15 if effective_elevation < 8.0 else 0.05)))
        st.write(f"Simulated Population Exposure: {flood_exposed_pop:,} residents affected.")

        st.markdown("---")
        st.subheader("14-Day Flood Stress Monitoring (Dynamic Simulation)")

        # Generate data and reverse the category array order so Day -1 is on the left
        multiplier = (base_pop % 4) + 2 + (simulated_water_rise * 0.4)
        stress_levels = [round(max(0.5, multiplier + (i * 0.15) + (0.3 * (i % 3))), 2) for i in range(14)]

        chart_df = pd.DataFrame({
            'Day Offset': [f"Day {i}" for i in range(-14, 0)],
            'Simulated Flood Stress Index': stress_levels,
            'SortKey': range(-14, 0)
        })
        chart_df = chart_df.sort_values('SortKey')

        # Reverse the array order so it displays Day -1 down to Day -14 left-to-right
        reversed_days = chart_df['Day Offset'].tolist()[::-1]

        fig = px.line(
            chart_df,
            x='Day Offset',
            y='Simulated Flood Stress Index',
            markers=True,
            template=None
        )
        style_chart(fig)
        fig.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            margin=dict(l=10, r=10, t=10, b=10),
            xaxis=dict(title="", categoryorder="array", categoryarray=reversed_days),
            yaxis=dict(title="Stress Index")
        )
        st.plotly_chart(fig, width="stretch")


    # ==========================================
    # PHASE 3: EMERGENCY PROTOCOLS & MITIGATION
    # ==========================================
    with st.container(key="phase-3"):
        phase_heading(3, "Emergency Protocols & Flood Response", st.session_state["selected_region_name"])

        st.error("**Flood Division Protocol**")
        st.write(f"Simulated water level ({effective_elevation}m effective) triggers automated pump station deployment and evacuation alerts across vulnerable sectors.")


render_scenario(current_topo, base_pop, st.session_state["selected_region_name"], tuple(active_bbox),
                start_date.isoformat(), end_date.isoformat(), analytics_provider)
