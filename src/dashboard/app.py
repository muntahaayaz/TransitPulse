"""
TransitPulse Dashboard

Premium dashboard shell built on top of the existing analytics layer.

Architecture:
Dashboard -> Analytics Layer -> Database
"""

from __future__ import annotations

import os
import sys

import streamlit as st

_PROJECT_ROOT = os.path.dirname(
    os.path.dirname(
        os.path.dirname(
            os.path.abspath(__file__)
        )
    )
)

if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from src.db.connection import get_engine

from src.analytics.analytics import (
    build_where,
    get_latest_records,
    get_metrics,
    get_pipeline_runs,
    get_route_distribution,
    get_timeline,
    get_top_stations,
    get_train_locations,
    get_line_reliability,
    get_station_delay_concentration,
    get_time_window_delay_concentration,
)

from src.analytics.sidebar import show_sidebar

from src.analytics.metrics import (
    show_metrics,
    show_recent_activity,
)

from src.analytics.charts import (
    show_live_map,
    show_route_distribution,
    show_timeline,
    show_top_routes,
    show_top_stations,
)

from src.analytics.tables import (
    show_latest_records,
    show_pipeline_history,
    show_route_leaderboard,
    show_station_leaderboard,
)


# ---------------------------------------------------------------------------
# Page configuration
# ---------------------------------------------------------------------------

st.set_page_config(
    page_title="TransitPulse",
    page_icon="🚇",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ---------------------------------------------------------------------------
# Premium visual system
# ---------------------------------------------------------------------------

st.markdown(
    """
    <style>
    /* ================================================================
       GLOBAL
       ================================================================ */

    :root {
        --tp-bg: #080b12;
        --tp-surface: #10151f;
        --tp-surface-2: #151b27;
        --tp-border: rgba(255,255,255,0.08);
        --tp-border-strong: rgba(255,255,255,0.13);
        --tp-text: #f5f7fb;
        --tp-muted: #8e99aa;
        --tp-accent: #35d5ff;
        --tp-green: #32e28b;
        --tp-yellow: #ffd166;
    }

    .stApp {
        background:
            radial-gradient(
                circle at 85% 0%,
                rgba(53,213,255,0.055),
                transparent 30%
            ),
            radial-gradient(
                circle at 15% 15%,
                rgba(77,96,255,0.045),
                transparent 28%
            ),
            var(--tp-bg);
        color: var(--tp-text);
    }

    .main .block-container {
        max-width: 1500px;
        padding-top: 2rem;
        padding-bottom: 4rem;
        padding-left: 3.2rem;
        padding-right: 3.2rem;
    }

    header[data-testid="stHeader"] {
        background: transparent;
    }

    /* ================================================================
       SIDEBAR
       ================================================================ */

    section[data-testid="stSidebar"] {
        background:
            linear-gradient(
                180deg,
                #0e131c 0%,
                #0a0e15 100%
            );
        border-right: 1px solid var(--tp-border);
    }

    section[data-testid="stSidebar"] > div {
        padding-top: 1.8rem;
    }

    section[data-testid="stSidebar"] h1,
    section[data-testid="stSidebar"] h2,
    section[data-testid="stSidebar"] h3 {
        color: var(--tp-text);
    }

    section[data-testid="stSidebar"] label {
        color: #b8c1cf !important;
        font-size: 0.82rem !important;
        font-weight: 600 !important;
    }

    section[data-testid="stSidebar"] div[data-baseweb="select"] > div {
        background: #111722;
        border-color: var(--tp-border-strong);
        border-radius: 10px;
    }

    /* ================================================================
       HERO
       ================================================================ */

    .tp-hero {
        position: relative;
        overflow: hidden;
        padding: 1.8rem 2rem 1.65rem 2rem;
        margin-bottom: 1.8rem;
        border: 1px solid var(--tp-border);
        border-radius: 18px;
        background:
            linear-gradient(
                135deg,
                rgba(20,30,44,0.98),
                rgba(11,16,25,0.98)
            );
        box-shadow:
            0 18px 50px rgba(0,0,0,0.22),
            inset 0 1px 0 rgba(255,255,255,0.025);
    }

    .tp-hero::after {
        content: "";
        position: absolute;
        width: 260px;
        height: 260px;
        right: -100px;
        top: -120px;
        border-radius: 50%;
        background: rgba(53,213,255,0.08);
        filter: blur(8px);
    }

    .tp-eyebrow {
        color: var(--tp-accent);
        font-size: 0.72rem;
        font-weight: 800;
        letter-spacing: 0.16em;
        text-transform: uppercase;
        margin-bottom: 0.55rem;
    }

    .tp-title {
        color: #ffffff;
        font-size: clamp(2rem, 4vw, 3.25rem);
        line-height: 1.05;
        font-weight: 800;
        letter-spacing: -0.045em;
        margin: 0;
    }

    .tp-subtitle {
        color: #9ca8ba;
        font-size: 0.98rem;
        margin-top: 0.7rem;
        margin-bottom: 1.2rem;
    }

    .tp-status-row {
        display: flex;
        align-items: center;
        gap: 0.65rem;
        flex-wrap: wrap;
    }

    .tp-status {
        display: inline-flex;
        align-items: center;
        gap: 0.45rem;
        padding: 0.42rem 0.75rem;
        border-radius: 999px;
        background: rgba(50,226,139,0.09);
        border: 1px solid rgba(50,226,139,0.18);
        color: #65e9a8;
        font-size: 0.75rem;
        font-weight: 700;
    }

    .tp-status-dot {
        width: 7px;
        height: 7px;
        border-radius: 50%;
        background: var(--tp-green);
        box-shadow: 0 0 12px rgba(50,226,139,0.8);
    }

    .tp-meta {
        color: #748095;
        font-size: 0.75rem;
    }

    /* ================================================================
       SECTION HEADERS
       ================================================================ */

    .tp-section {
        margin-top: 2.4rem;
        margin-bottom: 1rem;
    }

    .tp-section-kicker {
        color: var(--tp-accent);
        font-size: 0.68rem;
        font-weight: 800;
        letter-spacing: 0.14em;
        text-transform: uppercase;
        margin-bottom: 0.3rem;
    }

    .tp-section-title {
        color: #f5f7fb;
        font-size: 1.55rem;
        font-weight: 750;
        letter-spacing: -0.025em;
        margin: 0;
    }

    .tp-section-desc {
        color: var(--tp-muted);
        font-size: 0.82rem;
        margin-top: 0.35rem;
    }

    /* ================================================================
       STREAMLIT METRICS
       ================================================================ */

    div[data-testid="stMetric"] {
        background:
            linear-gradient(
                145deg,
                rgba(20,27,39,0.98),
                rgba(13,18,27,0.98)
            );
        border: 1px solid var(--tp-border);
        border-radius: 15px;
        padding: 1rem 1.1rem;
        min-height: 118px;
        box-shadow:
            0 12px 30px rgba(0,0,0,0.16),
            inset 0 1px 0 rgba(255,255,255,0.025);
    }

    div[data-testid="stMetric"] label {
        color: #8e99aa !important;
        font-size: 0.74rem !important;
        font-weight: 700 !important;
        text-transform: uppercase;
        letter-spacing: 0.06em;
    }

    div[data-testid="stMetric"] [data-testid="stMetricValue"] {
        color: #f7f9fc;
        font-weight: 800;
        letter-spacing: -0.035em;
    }

    /* ================================================================
       CHARTS / DATA CARDS
       ================================================================ */

    div[data-testid="stPlotlyChart"] {
        border: 1px solid var(--tp-border);
        border-radius: 15px;
        background: rgba(13,18,27,0.72);
        padding: 0.35rem;
        box-shadow: 0 12px 32px rgba(0,0,0,0.14);
    }

    div[data-testid="stDataFrame"] {
        border: 1px solid var(--tp-border);
        border-radius: 15px;
        overflow: hidden;
    }

    /* ================================================================
       ALERTS / INFO BOXES
       ================================================================ */

    div[data-testid="stAlert"] {
        border-radius: 13px;
        border: 1px solid var(--tp-border);
    }

    /* ================================================================
       DIVIDERS
       ================================================================ */

    hr {
        border: none !important;
        border-top: 1px solid rgba(255,255,255,0.07) !important;
        margin: 2.1rem 0 !important;
    }

    /* ================================================================
       FOOTER
       ================================================================ */

    .tp-footer {
        display: flex;
        justify-content: space-between;
        gap: 1rem;
        flex-wrap: wrap;
        padding: 1.2rem 0 0.4rem;
        color: #697487;
        font-size: 0.72rem;
    }

    .tp-footer strong {
        color: #9ba6b7;
    }

    /* ================================================================
       MOBILE
       ================================================================ */

    @media (max-width: 900px) {
        .main .block-container {
            padding-left: 1rem;
            padding-right: 1rem;
        }

        .tp-hero {
            padding: 1.35rem;
        }

        .tp-title {
            font-size: 2rem;
        }
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# ---------------------------------------------------------------------------
# Small UI helpers
# ---------------------------------------------------------------------------

def section_header(kicker: str, title: str, description: str = "") -> None:
    description_html = (
        f'<div class="tp-section-desc">{description}</div>'
        if description
        else ""
    )

    st.markdown(
        f"""
        <div class="tp-section">
            <div class="tp-section-kicker">{kicker}</div>
            <div class="tp-section-title">{title}</div>
            {description_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------------------------
# Hero
# ---------------------------------------------------------------------------

st.markdown(
    """
    <div class="tp-hero">
        <div class="tp-eyebrow">Transit intelligence platform</div>
        <div class="tp-title">TransitPulse</div>
        <div class="tp-subtitle">
            NYC Subway Reliability & Operations Intelligence
        </div>
        <div class="tp-status-row">
            <div class="tp-status">
                <span class="tp-status-dot"></span>
                LIVE DATA PIPELINE
            </div>
            <div class="tp-meta">
                Realtime feed monitoring · 30 second refresh
            </div>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)


# ---------------------------------------------------------------------------
# Application
# ---------------------------------------------------------------------------

try:
    engine = get_engine()

    # -----------------------------------------------------------------------
    # Sidebar / filters
    # -----------------------------------------------------------------------

    selected_route, selected_entity = show_sidebar(engine)

    where_clause = build_where(
        selected_route,
        selected_entity,
    )

    # -----------------------------------------------------------------------
    # Overview
    # -----------------------------------------------------------------------

    section_header(
        "01 / Network",
        "System Overview",
        "A live snapshot of the NYC subway data pipeline.",
    )

    metrics = get_metrics(engine)
    show_metrics(metrics)

    st.markdown("<div style='height:0.35rem'></div>", unsafe_allow_html=True)

    show_recent_activity(metrics)

    # -----------------------------------------------------------------------
    # Network analytics
    # -----------------------------------------------------------------------

    st.divider()

    section_header(
        "02 / Analytics",
        "Network Performance",
        "Distribution and activity across routes and stations.",
    )

    routes = get_route_distribution(
        engine,
        where_clause,
    )

    top_stops = get_top_stations(
        engine,
        where_clause,
    )

    chart_left, chart_right = st.columns(
        2,
        gap="large",
    )

    with chart_left:
        show_route_distribution(routes)

    with chart_right:
        show_top_routes(routes)

    st.markdown("<div style='height:0.8rem'></div>", unsafe_allow_html=True)

    show_top_stations(top_stops)

    # -----------------------------------------------------------------------
    # M2 Reliability Breakdown
    # -----------------------------------------------------------------------
    section_header(
        "03 / Reliability Breakdown",
        "Line, Station & Time Performance",
        "Reliability by subway line, delay concentration by station, and hourly delay patterns.",
    )

    reliability = get_line_reliability(engine)
    station_delays = get_station_delay_concentration(engine, limit=10)
    hourly_delays = get_time_window_delay_concentration(engine)

    st.subheader("Line Reliability")
    st.dataframe(reliability, use_container_width=True, hide_index=True)

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Stations with Highest Delay")
        st.dataframe(
            station_delays,
            use_container_width=True,
            hide_index=True,
        )

    with col2:
        st.subheader("Delay by Hour")
        st.dataframe(
            hourly_delays,
            use_container_width=True,
            hide_index=True,
        )

    st.markdown("<div style='height:0.8rem'></div>", unsafe_allow_html=True)

    # -----------------------------------------------------------------------
    # Operations timeline
    # -----------------------------------------------------------------------

    st.divider()

    section_header(
        "03 / Operations",
        "Operations Timeline",
        "Feed activity and network operating patterns over time.",
    )

    timeline = get_timeline(
        engine,
        where_clause,
    )

    show_timeline(timeline)

    # -----------------------------------------------------------------------
    # Live network
    # -----------------------------------------------------------------------

    st.divider()

    section_header(
        "04 / Live Network",
        "Live Network View",
        "Realtime train positions supplied by the feed.",
    )

    train_locations = get_train_locations(
        engine,
        where_clause,
    )

    show_live_map(train_locations)

    # -----------------------------------------------------------------------
    # Leaderboards
    # -----------------------------------------------------------------------

    st.divider()

    section_header(
        "05 / Rankings",
        "Performance Leaderboards",
        "Highest-volume routes and stations in the selected view.",
    )

    leaderboard_left, leaderboard_right = st.columns(
        2,
        gap="large",
    )

    with leaderboard_left:
        show_route_leaderboard(routes)

    with leaderboard_right:
        show_station_leaderboard(top_stops)

    # -----------------------------------------------------------------------
    # Latest feed records
    # -----------------------------------------------------------------------

    st.divider()

    section_header(
        "06 / Feed",
        "Latest Feed Records",
        "Most recently ingested realtime observations.",
    )

    latest = get_latest_records(
        engine,
        where_clause,
    )

    show_latest_records(latest)

    # -----------------------------------------------------------------------
    # Pipeline history
    # -----------------------------------------------------------------------

    st.divider()

    section_header(
        "07 / Reliability",
        "Pipeline History",
        "Recent ingestion runs and pipeline health.",
    )

    pipeline = get_pipeline_runs(engine)

    show_pipeline_history(pipeline)

    # -----------------------------------------------------------------------
    # Footer
    # -----------------------------------------------------------------------

    st.divider()

    st.markdown(
        """
        <div class="tp-footer">
            <div>
                <strong>TransitPulse</strong>
                &nbsp;·&nbsp; NYC Subway Intelligence
            </div>
            <div>
                PostgreSQL&nbsp; · &nbsp;Python&nbsp; · &nbsp;Streamlit&nbsp; · &nbsp;Plotly
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

finally:
    if "engine" in locals():
        engine.dispose()
