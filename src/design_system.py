"""Shared presentation primitives. Data and scenario calculations stay in the app.

Colors are semantic tokens in assets/theme.css; Streamlit's native theme menu
selects the matching dark/light base in .streamlit/config.toml. No extra theme
control is needed. Spacing uses a 4px scale; motion respects reduced motion.
"""
from html import escape
import json
from pathlib import Path

import streamlit as st


ASSETS = Path(__file__).resolve().parent.parent / "app" / "assets"
PALETTE = {
    "neutral": "#c5bba8",
    "signal": "#67d9e7",
    "warning": "#c5a066",
    "critical": "#b77a73",
    "success": "#8da997",
}


def apply_design_system():
    """Install shared tokens, layout, and progressive motion enhancements."""
    st.html(f"<style>{(ASSETS / 'theme.css').read_text(encoding='utf-8')}</style>")
    orbital = (ASSETS / "orbital.js").read_text(encoding="utf-8")
    orbital = orbital.replace("__FLOODER_LAND__", (ASSETS / "globe-land.json").read_text(encoding="utf-8"))
    controller = json.dumps(orbital + "\n" + (ASSETS / "interface.js").read_text(encoding="utf-8")).replace("</", "<\\/")
    # Bootstrap trusted project code through Streamlit's same-origin HTML frame.
    # CSS hides this one-pixel frame so the controller takes no visible space.
    st.iframe(
        '<!-- flooder-controller --><script>'
        'const script = parent.document.createElement("script");'
        f'script.textContent = {controller};'
        'parent.document.head.appendChild(script);script.remove();'
        '</script>',
        height=1,
        tab_index=-1,
    )


def render_phase_navigation():
    """Rehome the original three navigation links in a persistent left rail."""
    phases = (
        ("1", "Satellite & radar", "Satellite radar and flood map"),
        ("2", "Flood analytics", "Flood and terrain analytics"),
        ("3", "Emergency protocols", "Emergency protocols and flood response"),
    )
    links = "".join(
        f'<a class="phase-link" href="#phase-{number}" title="Phase {number}: {description}" '
        f'aria-label="Phase {number}: {description}">'
        f'<span class="phase-index" aria-hidden="true">0{number}</span>'
        f'<span class="phase-label"><span class="phase-number">Phase 0{number}</span>'
        f'{label}</span><span class="nav-indicator" aria-hidden="true"></span></a>'
        for number, label, description in phases
    )
    st.html(
        '<nav class="phase-navigation" aria-label="Phases">'
        '<div class="workspace-brand" aria-hidden="true"><span>FLOODER</span>'
        '<small>Geospatial workspace</small></div>'
        f'<div class="nav-section-label" aria-hidden="true">Operations / 03</div>{links}</nav>'
    )


def phase_heading(number, title, region=None):
    target = f'<span class="phase-target">{escape(region)}</span>' if region else ""
    st.html(
        f'<h2 id="phase-{number}" class="phase-heading">'
        f'<span class="section-index">0{number}</span>'
        f'<span>{escape(title)}</span>{target}</h2>'
    )


def status_message(message, severity):
    """Keep the existing alert, using the appropriate semantic presentation."""
    {"critical": st.error, "warning": st.warning, "success": st.success}.get(severity, st.info)(message)


def style_satellite_map(map_obj):
    """Style the existing map controls, tiles, and markers inside its iframe."""
    import folium

    map_css = (ASSETS / "map.css").read_text(encoding="utf-8")
    map_obj.get_root().header.add_child(folium.Element(f"<style>{map_css}</style>"))
    from src.map_controls import MapDisplayControl
    MapDisplayControl(map_obj).add_to(map_obj)


def map_marker(severity):
    import folium

    return folium.DivIcon(
        html=f'<span class="sensor-marker sensor-marker--{severity}"></span>',
        icon_size=(24, 24),
        icon_anchor=(12, 12),
        class_name="sensor-marker-anchor",
    )


def style_chart(figure):
    """Use the shared signal accent for traces, with a readable light variant."""
    accent = "#286a77" if st.context.theme.type == "light" else PALETTE["signal"]
    figure.update_traces(
        line=dict(color=accent, width=2, shape="spline", smoothing=0.45),
        marker=dict(size=5, color=accent),
    )
    figure.update_layout(
        template=None,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter, Segoe UI, sans-serif", size=11, color="#9b9992"),
        margin=dict(l=8, r=16, t=16, b=12),
        height=290,
        hovermode="x unified",
        transition=dict(duration=380, easing="cubic-in-out"),
        uirevision="hazard-stress",
    )
    figure.update_xaxes(showgrid=False, zeroline=False, tickfont=dict(size=10))
    figure.update_yaxes(gridcolor="rgba(149,145,133,0.12)", zeroline=False)
    return figure
