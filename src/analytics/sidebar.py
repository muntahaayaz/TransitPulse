"""
TransitPulse Sidebar

Professional sidebar filters for the dashboard.
"""

from __future__ import annotations

import streamlit as st

from src.analytics.analytics import (
    get_entity_types,
    get_routes,
)


def show_sidebar(conn):
    """Display TransitPulse sidebar filters.

    Returns
    -------
    tuple
        (selected_route, selected_entity)
    """

    st.sidebar.title("🔎 Filters")
    st.sidebar.caption("Refine the dashboard view")

    # -----------------------------------------------------------------------
    # Route Filter
    # -----------------------------------------------------------------------

    route_df = get_routes(conn)

    route_options = ["All"]

    if not route_df.empty and "route_id" in route_df.columns:
        route_options += (
            route_df["route_id"]
            .dropna()
            .astype(str)
            .sort_values()
            .tolist()
        )

    selected_route = st.sidebar.selectbox(
        "🚆 Subway Route",
        route_options,
        index=0,
    )

    # -----------------------------------------------------------------------
    # Entity Type Filter
    # -----------------------------------------------------------------------

    entity_df = get_entity_types(conn)

    entity_options = ["All"]

    if not entity_df.empty and "entity_type" in entity_df.columns:
        entity_options += (
            entity_df["entity_type"]
            .dropna()
            .astype(str)
            .sort_values()
            .tolist()
        )

    selected_entity = st.sidebar.selectbox(
        "📦 Entity Type",
        entity_options,
        index=0,
    )

    # -----------------------------------------------------------------------
    # Dashboard Status
    # -----------------------------------------------------------------------

    st.sidebar.markdown("---")

    st.sidebar.success(
        "🟢 Dashboard refreshes every 30 seconds."
    )

    # -----------------------------------------------------------------------
    # Current Filters
    # -----------------------------------------------------------------------

    st.sidebar.markdown("### Current Filters")

    route_display = (
        "All routes"
        if selected_route == "All"
        else selected_route
    )

    entity_display = (
        "All entity types"
        if selected_entity == "All"
        else selected_entity
    )

    st.sidebar.write(
        f"**Route:** {route_display}"
    )

    st.sidebar.write(
        f"**Entity:** {entity_display}"
    )

    # -----------------------------------------------------------------------
    # Footer
    # -----------------------------------------------------------------------

    st.sidebar.markdown("---")

    st.sidebar.caption(
        "TransitPulse • M1 Analytics Dashboard"
    )

    return (
        selected_route,
        selected_entity,
    )