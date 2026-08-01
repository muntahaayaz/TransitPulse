"""
M0 (Walking Skeleton) dashboard.

Deliberately minimal: this page proves the pipeline is alive end to end
(ingestion -> database -> dashboard), it does not compute reliability
metrics yet. Real on-time/delay analysis (FR-4 onward) arrives in M1 --
see ROADMAP.md.
"""
from __future__ import annotations

import os
import sys

import pandas as pd
import streamlit as st

# See src/ingestion/run_ingestion.py for why this specific sys.path
# adjustment (project root, not this file's own directory) is needed for
# direct-script execution to be consistent with -m execution and with
# absolute `from src.x import y` imports used everywhere else.
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from src.db.connection import get_connection, MissingDatabaseUrlError  # noqa: E402

st.set_page_config(page_title="TransitPulse (M0)", layout="centered")

st.title("TransitPulse")
st.caption(
    "M0 -- Walking Skeleton. This page confirms the ingestion pipeline is "
    "alive and writing real data. Reliability metrics (on-time %, delay "
    "breakdowns) arrive in M1."
)

try:
    conn = get_connection()

    total_records = pd.read_sql("SELECT count(*) AS n FROM raw_feed_event;", conn).iloc[0]["n"]
    st.metric("Total ingested records", int(total_records))

    latest_run = pd.read_sql(
        """
        SELECT started_at, finished_at, status, records_written, error_message
        FROM ingestion_run_log
        ORDER BY started_at DESC
        LIMIT 1;
        """,
        conn,
    )
    st.subheader("Most recent ingestion run")
    if latest_run.empty:
        st.info("No ingestion runs logged yet -- the workflow may not have executed.")
    else:
        st.dataframe(latest_run, hide_index=True, use_container_width=True)

    st.subheader("Most recent raw records")
    recent = pd.read_sql(
        """
        SELECT ingested_at, entity_type, route_id, stop_id
        FROM raw_feed_event
        ORDER BY ingested_at DESC
        LIMIT 20;
        """,
        conn,
    )
    if recent.empty:
        st.info("No records ingested yet.")
    else:
        st.dataframe(recent, hide_index=True, use_container_width=True)

    conn.close()

except MissingDatabaseUrlError as exc:
    st.error(str(exc))
except Exception as exc:  # noqa: BLE001
    st.error(f"Could not load data from the database: {exc}")
    st.caption("If this is the very first run, the ingestion workflow may not have executed yet.")
