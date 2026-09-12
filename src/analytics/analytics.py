"""
TransitPulse Analytics Layer

All SQL queries for the dashboard live here.

The dashboard should NEVER contain SQL directly.
It simply calls these helper functions.
"""

from __future__ import annotations


import pandas as pd


# --------------------------------------------------
# Dashboard Metrics
# --------------------------------------------------

def get_metrics(conn) -> dict:
    """Return dashboard KPI metrics."""

    total_events = pd.read_sql(
        """
        SELECT COUNT(*) AS value
        FROM raw_feed_event;
        """,
        conn,
    ).iloc[0]["value"]

    total_routes = pd.read_sql(
        """
        SELECT COUNT(DISTINCT route_id) AS value
        FROM raw_feed_event
        WHERE route_id IS NOT NULL;
        """,
        conn,
    ).iloc[0]["value"]

    total_stops = pd.read_sql(
        """
        SELECT COUNT(DISTINCT stop_id) AS value
        FROM raw_feed_event
        WHERE stop_id IS NOT NULL;
        """,
        conn,
    ).iloc[0]["value"]

    last_update = pd.read_sql(
        """
        SELECT MAX(ingested_at) AS value
        FROM raw_feed_event;
        """,
        conn,
    ).iloc[0]["value"]

    return {
        "events": int(total_events),
        "routes": int(total_routes),
        "stops": int(total_stops),
        "last_update": last_update,
    }


# --------------------------------------------------
# Sidebar Data
# --------------------------------------------------

def get_routes(conn):

    return pd.read_sql(
        """
        SELECT DISTINCT route_id
        FROM raw_feed_event
        WHERE route_id IS NOT NULL
        ORDER BY route_id;
        """,
        conn,
    )


def get_entity_types(conn):

    return pd.read_sql(
        """
        SELECT DISTINCT entity_type
        FROM raw_feed_event
        ORDER BY entity_type;
        """,
        conn,
    )


# --------------------------------------------------
# Build WHERE clause
# --------------------------------------------------

def build_where(route="All", entity="All"):

    conditions = []

    if route != "All":
        conditions.append(f"route_id='{route}'")

    if entity != "All":
        conditions.append(f"entity_type='{entity}'")

    if not conditions:
        return ""

    return "WHERE " + " AND ".join(conditions)


# --------------------------------------------------
# Route Distribution
# --------------------------------------------------

def get_route_distribution(conn, where_clause=""):

    query = f"""
    SELECT
        route_id,
        COUNT(*) AS records
    FROM raw_feed_event
    {where_clause}
    GROUP BY route_id
    ORDER BY records DESC;
    """

    return pd.read_sql(query, conn)


# --------------------------------------------------
# Top Stations
# --------------------------------------------------

def get_top_stations(conn, where_clause=""):

    query = f"""
    SELECT
        stop_id,
        COUNT(*) AS records
    FROM raw_feed_event
    {where_clause}
    GROUP BY stop_id
    ORDER BY records DESC
    LIMIT 10;
    """

    return pd.read_sql(query, conn)


# --------------------------------------------------
# Latest Records
# --------------------------------------------------

def get_latest_records(conn, where_clause=""):

    query = f"""
    SELECT
        ingested_at,
        entity_type,
        route_id,
        stop_id
    FROM raw_feed_event
    {where_clause}
    ORDER BY ingested_at DESC
    LIMIT 20;
    """

    return pd.read_sql(query, conn)


# --------------------------------------------------
# Pipeline Runs
# --------------------------------------------------

def get_pipeline_runs(conn):

    return pd.read_sql(
        """
        SELECT
            started_at,
            finished_at,
            status,
            records_written
        FROM ingestion_run_log
        ORDER BY started_at DESC
        LIMIT 20;
        """,
        conn,
    )


# --------------------------------------------------
# Feed Activity Timeline
# --------------------------------------------------

def get_timeline(conn, where_clause=""):
    """
    Feed events grouped by minute.
    Used for the timeline chart.
    """

    query = f"""
    SELECT
        DATE_TRUNC('minute', ingested_at) AS minute,
        COUNT(*) AS records
    FROM raw_feed_event
    {where_clause}
    GROUP BY minute
    ORDER BY minute;
    """

    return pd.read_sql(query, conn)


# --------------------------------------------------
# Live Train Map Data
# --------------------------------------------------

def get_train_locations(conn, where_clause=""):
    """
    Return train locations for the interactive map.
    """

    if where_clause:
        where_clause = (
            where_clause
            + " AND vehicle_lat IS NOT NULL"
            + " AND vehicle_lon IS NOT NULL"
        )
    else:
        where_clause = (
            "WHERE vehicle_lat IS NOT NULL"
            " AND vehicle_lon IS NOT NULL"
        )

    query = f"""
    SELECT
        vehicle_lat,
        vehicle_lon,
        route_id,
        stop_id,
        entity_type
    FROM raw_feed_event
    {where_clause};
    """

    return pd.read_sql(query, conn)