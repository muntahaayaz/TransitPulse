"""
TransitPulse Charts

Reusable Plotly and PyDeck chart components.
"""

from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import pydeck as pdk
import streamlit as st


# ---------------------------------------------------------------------------
# Shared chart styling
# ---------------------------------------------------------------------------

_CHART_HEIGHT = 400

_LAYOUT = {
    "margin": dict(l=20, r=30, t=20, b=20),
    "paper_bgcolor": "rgba(0,0,0,0)",
    "plot_bgcolor": "rgba(0,0,0,0)",
    "font": dict(
        family="Inter, Arial, sans-serif",
        size=13,
    ),
}

_GRID = {
    "showgrid": True,
    "gridcolor": "rgba(128,128,128,0.15)",
    "zeroline": False,
}


def _apply_layout(
    fig: go.Figure,
    *,
    height: int = _CHART_HEIGHT,
) -> go.Figure:
    """Apply the shared TransitPulse chart appearance."""

    layout = {
        **_LAYOUT,
        "height": height,
    }

    fig.update_layout(**layout)

    fig.update_xaxes(
        **_GRID,
        showline=False,
    )

    fig.update_yaxes(
        **_GRID,
        showline=False,
    )

    return fig


def _chart_config() -> dict:
    """Return consistent Plotly configuration."""

    return {
        "displayModeBar": False,
        "responsive": True,
    }


def _empty_state(message: str) -> None:
    """Display a consistent empty-data state."""

    st.info(message)


# ---------------------------------------------------------------------------
# Route Distribution
# ---------------------------------------------------------------------------


def show_route_distribution(routes: pd.DataFrame) -> None:
    """Display the share of feed events by route."""

    st.subheader("🥧 Route Distribution")

    if routes.empty:
        _empty_state(
            "No route distribution data available."
        )
        return

    data = routes.copy()

    data["route_id"] = data["route_id"].astype(str)

    fig = px.pie(
        data,
        values="records",
        names="route_id",
        hole=0.60,
    )

    fig.update_traces(
        textposition="inside",
        textinfo="percent",
        hovertemplate=(
            "<b>Route %{label}</b><br>"
            "Feed events: %{value:,}<br>"
            "Share: %{percent}<extra></extra>"
        ),
        marker=dict(
            line=dict(
                color="rgba(255,255,255,0.75)",
                width=1,
            )
        ),
    )

    _apply_layout(
        fig,
        height=400,
    )

    fig.update_layout(
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="top",
            y=-0.04,
            xanchor="center",
            x=0.5,
            font=dict(size=12),
        ),
    )

    st.plotly_chart(
        fig,
        width="stretch",
        config=_chart_config(),
    )


# ---------------------------------------------------------------------------
# Top Routes
# ---------------------------------------------------------------------------


def show_top_routes(routes: pd.DataFrame) -> None:
    """Display routes ranked by feed activity."""

    st.subheader("🚆 Top Routes")

    if routes.empty:
        _empty_state(
            "No route activity data available."
        )
        return

    data = (
        routes
        .sort_values(
            "records",
            ascending=True,
        )
        .copy()
    )

    data["route_id"] = data["route_id"].astype(str)

    fig = px.bar(
        data,
        x="records",
        y="route_id",
        orientation="h",
        text="records",
    )

    fig.update_traces(
        textposition="outside",
        cliponaxis=False,
        hovertemplate=(
            "<b>Route %{y}</b><br>"
            "Feed events: %{x:,}<extra></extra>"
        ),
    )

    _apply_layout(
        fig,
        height=max(
            360,
            len(data) * 42,
        ),
    )

    fig.update_layout(
        xaxis_title=None,
        yaxis_title=None,
        showlegend=False,
        xaxis=dict(
            tickformat=",",
        ),
    )

    st.plotly_chart(
        fig,
        width="stretch",
        config=_chart_config(),
    )


# ---------------------------------------------------------------------------
# Top Stations
# ---------------------------------------------------------------------------


def show_top_stations(stops: pd.DataFrame) -> None:
    """Display stations ranked by feed activity."""

    st.subheader("📍 Top Stations")

    if stops.empty:
        _empty_state(
            "No station activity data available."
        )
        return

    data = (
        stops
        .sort_values(
            "records",
            ascending=True,
        )
        .copy()
    )

    data["stop_id"] = data["stop_id"].astype(str)

    fig = px.bar(
        data,
        x="records",
        y="stop_id",
        orientation="h",
        text="records",
    )

    fig.update_traces(
        textposition="outside",
        cliponaxis=False,
        hovertemplate=(
            "<b>Station %{y}</b><br>"
            "Feed events: %{x:,}<extra></extra>"
        ),
    )

    _apply_layout(
        fig,
        height=max(
            420,
            len(data) * 36,
        ),
    )

    fig.update_layout(
        xaxis_title=None,
        yaxis_title=None,
        showlegend=False,
        xaxis=dict(
            tickformat=",",
        ),
    )

    st.plotly_chart(
        fig,
        width="stretch",
        config=_chart_config(),
    )


# ---------------------------------------------------------------------------
# Feed Timeline
# ---------------------------------------------------------------------------


def show_timeline(timeline: pd.DataFrame) -> None:
    """Display feed activity over time."""

    st.subheader("📈 Feed Activity")

    if timeline.empty:
        _empty_state(
            "No feed activity available for the selected period."
        )
        return

    data = (
        timeline
        .sort_values("minute")
        .copy()
    )

    data["minute"] = pd.to_datetime(
        data["minute"],
        errors="coerce",
    )

    data = data.dropna(
        subset=["minute"],
    )

    if data.empty:
        _empty_state(
            "No valid timeline data available."
        )
        return

    fig = px.line(
        data,
        x="minute",
        y="records",
        markers=True,
    )

    fig.update_traces(
        mode="lines+markers",
        line=dict(width=3),
        marker=dict(size=6),
        hovertemplate=(
            "<b>%{x|%b %d, %Y %H:%M}</b><br>"
            "Feed events: %{y:,}<extra></extra>"
        ),
    )

    _apply_layout(
        fig,
        height=400,
    )

    fig.update_layout(
        xaxis_title=None,
        yaxis_title="Feed events",
        hovermode="x unified",
        showlegend=False,
        yaxis=dict(
            tickformat=",",
        ),
    )

    st.plotly_chart(
        fig,
        width="stretch",
        config=_chart_config(),
    )



# ---------------------------------------------------------------------------
# Delay by Hour
# ---------------------------------------------------------------------------


def show_delay_by_hour(hourly_delays: pd.DataFrame) -> None:
    """Display average delay by hour of day."""

    st.subheader("Delay by Hour")

    if hourly_delays.empty:
        _empty_state(
            "No hourly delay data available."
        )
        return

    data = hourly_delays.copy()
    data["hour"] = data["hour"].astype(int)

    fig = px.bar(
        data,
        x="hour",
        y="average_delay_minutes",
        text="average_delay_minutes",
        labels={
            "hour": "Hour of Day",
            "average_delay_minutes": "Average Delay (minutes)",
        },
    )

    fig.update_traces(
        hovertemplate=(
            "<b>%{x}:00</b><br>"
            "Average delay: %{y:.2f} min"
            "<extra></extra>"
        ),
        texttemplate="%{y:.2f}",
        textposition="outside",
    )

    _apply_layout(
        fig,
        height=400,
    )

    fig.update_xaxes(
        dtick=1,
        tickmode="linear",
        title_text="Hour of Day",
    )

    fig.update_yaxes(
        title_text="Average Delay (minutes)",
    )

    st.plotly_chart(
        fig,
        width="stretch",
        config=_chart_config(),
    )



# ---------------------------------------------------------------------------
# Live Subway Map
# ---------------------------------------------------------------------------


def show_live_map(train_df: pd.DataFrame) -> None:
    """Display an interactive live subway map."""

    st.subheader("🗺️ Live Train Map")

    if train_df.empty:
        st.info(
            "🚇 No live train locations are currently available."
        )

        st.caption(
            "Live vehicle coordinates will appear here when "
            "the feed provides valid location data."
        )

        return

    data = (
        train_df
        .rename(
            columns={
                "vehicle_lat": "lat",
                "vehicle_lon": "lon",
            }
        )
        .copy()
    )

    data = data.dropna(
        subset=["lat", "lon"],
    )

    if data.empty:
        st.info(
            "🚇 No valid train coordinates are currently available."
        )

        st.caption(
            "The feed is available, but no usable vehicle "
            "coordinates were returned."
        )

        return

    view_state = pdk.ViewState(
        latitude=float(
            data["lat"].mean()
        ),
        longitude=float(
            data["lon"].mean()
        ),
        zoom=10.5,
        pitch=35,
    )

    layer = pdk.Layer(
        "ScatterplotLayer",
        data=data,
        get_position="[lon, lat]",
        get_fill_color=[255, 80, 80, 190],
        get_radius=110,
        pickable=True,
        auto_highlight=True,
    )

    tooltip = {
        "html": """
        <div style="
            font-family: Arial, sans-serif;
            line-height: 1.6;
        ">
            <b>Route:</b> {route_id}<br/>
            <b>Stop:</b> {stop_id}<br/>
            <b>Entity:</b> {entity_type}
        </div>
        """,
        "style": {
            "backgroundColor": "#111827",
            "color": "white",
            "fontSize": "13px",
            "padding": "10px",
            "borderRadius": "8px",
        },
    }

    deck = pdk.Deck(
        map_style="dark",
        initial_view_state=view_state,
        layers=[layer],
        tooltip=tooltip,
    )

    st.pydeck_chart(
        deck,
        width="stretch",
    )

    count = len(data)

    st.caption(
        f"{count:,} live vehicle location"
        f"{'' if count == 1 else 's'} displayed"
    )


def show_reliability_trend(trend: pd.DataFrame) -> None:
    """Display weekly historical reliability trend."""
    st.subheader("Historical Reliability Trend")

    if trend.empty:
        _empty_state("No historical reliability data available.")
        return

    data = trend.copy()

    fig = px.line(
        data,
        x="week",
        y="on_time_percent",
        markers=True,
        labels={
            "week": "Week",
            "on_time_percent": "On-Time Performance (%)",
        },
    )

    fig.update_traces(
        hovertemplate=(
            "<b>%{x}</b><br>"
            "On-time: %{y:.1f}%"
            "<extra></extra>"
        ),
    )

    _apply_layout(fig, height=400)
    fig.update_xaxes(title_text="Week")
    fig.update_yaxes(
        title_text="On-Time Performance (%)",
        range=[0, 100],
    )

    st.plotly_chart(
        fig,
        width="stretch",
        config=_chart_config(),
    )
