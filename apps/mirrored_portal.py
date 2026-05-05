import streamlit as st
import plotly.graph_objects as go
import json
import os
import asyncio
from tools.stellarium_bridge import StellariumBridge

# Executive UI Configuration
st.set_page_config(page_title="A2A World | Mirrored Portal", layout="wide")

st.markdown("""
<style>
    .main {background-color: #0E1117;}
    h1 {color: #00FF41; font-family: 'Courier New', monospace; text-shadow: 0 0 10px #00FF41;}
    h2, h3 {color: #E6E6E6; font-family: 'Courier New', monospace;}
    .stMetric {background-color: #161B22; padding: 10px; border-radius: 5px; border: 1px solid #00FF41;}
    .stButton>button {width: 100%; background-color: #161B22; color: #00FF41; border: 1px solid #00FF41;}
</style>
""", unsafe_allow_html=True)

st.title("🌍 A2A WORLD: THE MIRRORED PORTAL")
st.subheader("Subject: Hamsa (Consensus Certified A2A-HAMSA-2026-0504-01)")

# --- ASTRAL SYNC ENGINE ---
bridge = StellariumBridge()

async def trigger_sync(lat, lon, target):
    resp = await bridge.set_location(lat, lon, name="Hamsa_POV")
    await bridge.focus_object(target)
    return resp

# --- MOCK DATA ---
mock_legend = {
    "lat": 37.6, "lon": 45.3,
    "consensus_score": 0.942,
    "p_value": 0.00018,
    "axial_lock": 23.5,
    "target_object": "Cygnus",
    "epoch": "-4000 BCE",
    "agents": ["GeoPatternAgent_VIA", "AstroAnalystAgent_VIA", "ConsensusCoordinator_VIA"]
}

# --- CONTROL PANEL ---
with st.sidebar:
    st.title("🛰️ MISSION CONTROL")
    if st.button("📡 SYNC STELLARIUM DESKTOP"):
        with st.spinner("Transmitting POV to Stellarium..."):
            asyncio.run(trigger_sync(mock_legend['lat'], mock_legend['lon'], mock_legend['target_object']))
            st.success("Stellarium Desktop Synchronized.")

    st.divider()
    st.metric("EPOCH OF RESONANCE", mock_legend['epoch'])
    st.divider()
    st.title("📊 FORENSIC AUDIT")
    st.sidebar.metric("CONSENSUS SCORE", f"{mock_legend['consensus_score']*100}%")
    st.sidebar.metric("P-VALUE", mock_legend['p_value'])
    st.sidebar.divider()
    st.sidebar.subheader("Verified Agent Cluster")
    for agent in mock_legend['agents']:
        st.sidebar.code(agent)

# --- VISUAL RESONANCE PANE ---
col1, col2 = st.columns(2)

with col1:
    st.header("🛰️ Terrestrial Geoglyph (KML)")
    fig_map = go.Figure(go.Scattermapbox(
        lat=[37.6, 37.7, 37.5, 37.6],
        lon=[45.3, 45.4, 45.4, 45.3],
        mode='lines',
        fill="toself",
        name="Hamsa Silhouette",
        marker=go.scattermapbox.Marker(size=10, color='#00FF41')
    ))
    fig_map.update_layout(
        mapbox_style="carto-darkmatter",
        mapbox_center_lat=37.6,
        mapbox_center_lon=45.3,
        mapbox_zoom=7,
        margin={"r":0,"t":0,"l":0,"b":0},
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)'
    )
    st.plotly_chart(fig_map, use_container_width=True)

with col2:
    st.header("✨ Embedded Sky Viewer (Aladin)")
    # Using Aladin Lite for integrated web view
    # Embed as HTML component
    aladin_html = f"""
    <div id="aladin-lite-div" style="width:100%;height:450px;"></div>
    <script src="https://aladin.u-strasbg.fr/AladinLite/api/v3/latest/aladin.js" charset="utf-8"></script>
    <script type="text/javascript">
        let aladin = A.aladin('#aladin-lite-div', {{survey: "P/DSS2/color", fov: 60, target: "{mock_legend['target_object']}"}});
        aladin.setProjection("AIT");
    </script>
    """
    st.components.v1.html(aladin_html, height=480)
    st.caption(f"Real-time celestial reference for {mock_legend['target_object']} ( DSS2 Color Survey )")

st.info(f"The Hamsa geoglyph's placement aligns with the constellation Cygnus at the {mock_legend['epoch']} epoch under the 23.5° axial lock.")
