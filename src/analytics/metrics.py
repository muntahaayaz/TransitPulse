"""
TransitPulse Metrics Components

Displays KPI cards and recent dashboard activity.
"""

from __future__ import annotations

import streamlit as st


# ---------------------------------------------------------------------------
# KPI Metrics
# ---------------------------------------------------------------------------


def show_metrics(metrics: dict) -> None:
    """Display the main TransitPulse KPI cards.

    Expected keys:
        events
        routes
        stops
        last_update
    """

    c1, c2, c3, c4 = st.columns(4)

    with c1:
        st.metric(
            label="📦 Total Feed Events",
            value=f"{metrics['events']:,}",
        )

    with c2:
        st.metric(
            label="🚆 Active Subway Lines",
            value=f"{metrics['routes']:,}",
        )

    with c3:
        st.metric(
            label="📍 Active Stations",
            value=f"{metrics['stops']:,}",
        )

    with c4:
        st.metric(
            label="🕒 Last Feed Update",
            value=str(metrics["last_update"]),
        )


# ---------------------------------------------------------------------------
# Recent Activity
# ---------------------------------------------------------------------------


def show_recent_activity(metrics: dict) -> None:
    """Display a compact recent-activity summary."""

    st.subheader("📈 Recent Activity")

    a1, a2, a3 = st.columns(3)

    with a1:
        st.info(
            f"**Last Feed Update**\n\n"
            f"{metrics['last_update']}"
        )

    with a2:
        st.success(
            f"**Active Routes**\n\n"
            f"{metrics['routes']:,}"
        )

    with a3:
        st.warning(
            f"**Active Stations**\n\n"
            f"{metrics['stops']:,}"
        )