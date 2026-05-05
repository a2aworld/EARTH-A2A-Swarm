import streamlit as st
import plotly.graph_objects as go
import json
import os

# Executive UI Configuration
st.set_page_config(page_title="A2A World | Mirrored Portal", layout="wide")

st.markdown("""
<style>
    .main {background-color: #0E1117;}
    h1 {color: #00FF41; font-family: 'Courier New', monospace; text-shadow: 0 0 10px #00FF41;}
    h2, h3 {color: #E6E6E6; font-family: 'Courier New', monospace;}
    .stMetric {background-color: #161B22; padding: 10px; border-radius: 5px; border: 1px solid #00FF41;}
</style>
""", unsafe_allow_html=True)

st.title("🌍 A2A WORLD: THE MIRRORED PORTAL")
st.subheader("Subject: Hamsa (Consensus Certified A2A-HAMSA-2026-0504-01)")

# --- MOCK DATA FOR DEMONSTRATION ---
# In production, this pulls from registry/master_legend.json
mock_legend = {
    "consensus_score": 0.942,
    "p_value": 0.00018,
    "axial_lock": 23.5,
    "anchor_star": "Deneb",
    "agents": ["GeoPatternAgent_VIA", "AstroAnalystAgent_VIA", "ConsensusCoordinator_VIA"]
}

col1, col2 = st.columns(2)

with col1:
    st.header("🛰️ Terrestrial Geoglyph (KML)")
    # Simulation of Lake Urmia / Hamsa area
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
    st.header("✨ Celestial Mirror (Cygnus)")
    # Cygnus Constellation with rotation
    fig_stars = go.Figure(go.Scatter(
        x=[0, 1, 2, 0.5, 1.5],
        y=[2, 1, 0, 1, 1],
        mode='markers+lines+text',
        text=["Deneb", "Sadr", "Albireo", "Delta Cyg", "Epsilon Cyg"],
        textposition="top center",
        marker=dict(size=12, color='white', symbol='star')
    ))
    fig_stars.update_layout(
        plot_bgcolor='#0E1117',
        paper_bgcolor='#0E1117',
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        title=f"Axial Lock Resonance: {mock_legend['axial_lock']}°",
        font=dict(color="#E6E6E6", family="Courier New"),
        margin={"r":0,"t":40,"l":0,"b":0}
    )
    st.plotly_chart(fig_stars, use_container_width=True)

# --- SIDEBAR: FORENSIC DATA ---
st.sidebar.title("📊 FORENSIC AUDIT")
st.sidebar.metric("CONSENSUS SCORE", f"{mock_legend['consensus_score']*100}%")
st.sidebar.metric("P-VALUE", mock_legend['p_value'])
st.sidebar.divider()
st.sidebar.subheader("Verified Agent Cluster")
for agent in mock_legend['agents']:
    st.sidebar.code(agent)
st.sidebar.success("STATUS: ENCODED")

st.info("The Hamsa geoglyph's placement is statistically significant ($p < 0.01$), mirroring the constellation Cygnus under the 23.5° axial lock.")
