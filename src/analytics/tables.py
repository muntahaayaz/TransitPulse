"""
TransitPulse Tables

Reusable dashboard tables and leaderboards.
"""

from __future__ import annotations

import pandas as pd
import streamlit as st


# ---------------------------------------------------------------------------
# Shared Helpers
# ---------------------------------------------------------------------------


def _empty_state(message: str) -> None:
    """Display a consistent empty-data state."""
    st.info(message)


def _prepare_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Return a safe copy for display."""
    if df is None:
        return pd.DataFrame()

    return df.copy()


# ---------------------------------------------------------------------------
# Latest Feed Events
# ---------------------------------------------------------------------------


def show_latest_records(df: pd.DataFrame) -> None:
    """Display the latest feed events."""

    st.subheader("📄 Latest Feed Events")

    data = _prepare_dataframe(df)

    if data.empty:
        _empty_state("No feed records available.")
        return

    st.dataframe(
        data,
        width="stretch",
        hide_index=True,
        use_container_width=None,
    )


# ---------------------------------------------------------------------------
# Top Stations Table
# ---------------------------------------------------------------------------


def show_top_station_table(df: pd.DataFrame) -> None:
    """Display the top stations table."""

    st.subheader("📍 Top Stations")

    data = _prepare_dataframe(df)

    if data.empty:
        _empty_state("No station data available.")
        return

    st.dataframe(
        data,
        width="stretch",
        hide_index=True,
        use_container_width=None,
    )


# ---------------------------------------------------------------------------
# Route Leaderboard
# ---------------------------------------------------------------------------


def show_route_leaderboard(routes: pd.DataFrame) -> None:
    """Display the top five subway routes."""

    st.subheader("🏆 Top Subway Routes")

    data = _prepare_dataframe(routes)

    if data.empty:
        _empty_state("No route data available.")
        return

    leaderboard = (
        data.sort_values(
            "records",
            ascending=False,
        )
        .head(5)
        .reset_index(drop=True)
    )

    leaderboard.index = range(1, len(leaderboard) + 1)

    st.dataframe(
        leaderboard,
        width="stretch",
        hide_index=False,
    )


# ---------------------------------------------------------------------------
# Station Leaderboard
# ---------------------------------------------------------------------------


def show_station_leaderboard(stops: pd.DataFrame) -> None:
    """Display the top five stations."""

    st.subheader("🚉 Top Subway Stations")

    data = _prepare_dataframe(stops)

    if data.empty:
        _empty_state("No station data available.")
        return

    leaderboard = (
        data.sort_values(
            "records",
            ascending=False,
        )
        .head(5)
        .reset_index(drop=True)
    )

    leaderboard.index = range(1, len(leaderboard) + 1)

    st.dataframe(
        leaderboard,
        width="stretch",
        hide_index=False,
    )


# ---------------------------------------------------------------------------
# Pipeline History
# ---------------------------------------------------------------------------


def show_pipeline_history(df: pd.DataFrame) -> None:
    """Display recent pipeline ingestion history."""

    st.subheader("⚡ Pipeline History")

    data = _prepare_dataframe(df)

    if data.empty:
        _empty_state("No pipeline history available.")
        return

    st.dataframe(
        data,
        width="stretch",
        hide_index=True,
        use_container_width=None,
    )