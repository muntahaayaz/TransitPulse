"""
TransitPulse ingestion driver.

Polls the MTA GTFS-Realtime feed for a bounded period and writes
parsed observations to PostgreSQL.

The driver is designed for both:
    python -m src.ingestion.run_ingestion
and direct script execution.
"""

from __future__ import annotations

import logging
import os
import sys
import time
from datetime import datetime, timezone

from psycopg2 import OperationalError, InterfaceError
from psycopg2.extras import execute_values

# ---------------------------------------------------------------------------
# Project import path
# ---------------------------------------------------------------------------

_PROJECT_ROOT = os.path.dirname(
    os.path.dirname(
        os.path.dirname(
            os.path.abspath(__file__)
        )
    )
)

if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from src.db.connection import get_connection  # noqa: E402
from src.ingestion.poll_feed import (  # noqa: E402
    ParsedEntity,
    fetch_feed,
    parse_feed,
)

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

POLL_INTERVAL_SECONDS = int(
    os.environ.get("POLL_INTERVAL_SECONDS", "30")
)

RUN_DURATION_SECONDS = int(
    os.environ.get("RUN_DURATION_SECONDS", str(8 * 60))
)

RAW_EVENT_RETENTION_DAYS = int(
    os.environ.get("RAW_EVENT_RETENTION_DAYS", "3")
)

# ---------------------------------------------------------------------------
# Connection helpers
# ---------------------------------------------------------------------------


def _connection_is_usable(conn) -> bool:
    """
    Return True when the psycopg2 connection is open and responsive.
    """

    if conn is None:
        return False

    if conn.closed:
        return False

    try:
        with conn.cursor() as cur:
            cur.execute("SELECT 1;")
            cur.fetchone()

        return True

    except (OperationalError, InterfaceError):
        return False

    except Exception:
        logger.exception(
            "Unexpected error while checking database connection."
        )
        return False


def _close_connection(conn) -> None:
    """
    Safely close a PostgreSQL connection.
    """

    if conn is None:
        return

    try:
        if not conn.closed:
            conn.close()
    except Exception:
        logger.exception(
            "Failed to close database connection."
        )


def _get_healthy_connection(conn):
    """
    Return the existing healthy connection or establish a new one.
    """

    if _connection_is_usable(conn):
        return conn

    if conn is not None:
        logger.warning(
            "Existing PostgreSQL connection is unavailable; reconnecting..."
        )
        _close_connection(conn)

    new_conn = get_connection()

    logger.info(
        "PostgreSQL connection established/re-established."
    )

    return new_conn


# ---------------------------------------------------------------------------
# Main ingestion run
# ---------------------------------------------------------------------------


def run() -> int:
    """
    Run one bounded ingestion workflow.

    Returns:
        0 when the run completes without poll failures.
        1 when the run has a complete or partial failure.
    """

    started_at = datetime.now(timezone.utc)

    total_written = 0
    status = "success"
    error_message: str | None = None

    conn = None

    # -----------------------------------------------------------------------
    # Initial database connection
    # -----------------------------------------------------------------------

    try:
        conn = get_connection()

        logger.info(
            "Database connection established."
        )

    except Exception:
        logger.exception(
            "Could not obtain a database connection; aborting run."
        )
        return 1

    # -----------------------------------------------------------------------
    # Polling loop
    # -----------------------------------------------------------------------

    try:
        deadline = time.monotonic() + RUN_DURATION_SECONDS

        logger.info(
            "Starting ingestion run: duration=%ss interval=%ss retention=%sd",
            RUN_DURATION_SECONDS,
            POLL_INTERVAL_SECONDS,
            RAW_EVENT_RETENTION_DAYS,
        )

        while time.monotonic() < deadline:
            cycle_start = time.monotonic()

            try:
                # -----------------------------------------------------------
                # Make sure PostgreSQL is still available.
                # -----------------------------------------------------------

                conn = _get_healthy_connection(conn)

                # -----------------------------------------------------------
                # Fetch
                # -----------------------------------------------------------

                logger.info(
                    "Fetching MTA GTFS-RT feed..."
                )

                raw_bytes = fetch_feed()

                logger.info(
                    "Received %.2f MB of feed data.",
                    len(raw_bytes) / (1024 * 1024),
                )

                # -----------------------------------------------------------
                # Parse
                # -----------------------------------------------------------

                records = parse_feed(raw_bytes)

                logger.info(
                    "Parsed %d feed records.",
                    len(records),
                )

                # -----------------------------------------------------------
                # Write
                # -----------------------------------------------------------

                try:
                    written = _write_records(
                        conn,
                        records,
                    )

                except (OperationalError, InterfaceError) as exc:
                    logger.warning(
                        "Database connection failed during write: %s",
                        exc,
                    )

                    _close_connection(conn)
                    conn = None

                    logger.info(
                        "Reconnecting to PostgreSQL and retrying write..."
                    )

                    conn = get_connection()

                    logger.info(
                        "PostgreSQL reconnected successfully."
                    )

                    written = _write_records(
                        conn,
                        records,
                    )

                total_written += written

                logger.info(
                    "Wrote %d records this cycle. Total=%d",
                    written,
                    total_written,
                )

            except Exception as exc:
                logger.exception(
                    "Poll cycle failed: %s",
                    exc,
                )

                status = "partial_failure"
                error_message = str(exc)

                if conn is not None and not conn.closed:
                    try:
                        conn.rollback()
                    except Exception:
                        logger.exception(
                            "Database rollback failed."
                        )

                if conn is not None and conn.closed:
                    conn = None

            elapsed = time.monotonic() - cycle_start

            sleep_seconds = max(
                0,
                POLL_INTERVAL_SECONDS - elapsed,
            )

            if sleep_seconds > 0:
                time.sleep(sleep_seconds)

    except KeyboardInterrupt:
        logger.warning(
            "Ingestion run interrupted by user."
        )

        status = "partial_failure"
        error_message = "Interrupted by user."

    except Exception as exc:
        logger.exception(
            "Ingestion run failed entirely: %s",
            exc,
        )

        status = "failure"
        error_message = str(exc)

    finally:
        # -------------------------------------------------------------------
        # Log run result
        # -------------------------------------------------------------------

        if conn is not None and not conn.closed:
            _log_run(
                conn,
                started_at,
                status,
                total_written,
                error_message,
            )

        else:
            logger.warning(
                "Skipping ingestion_run_log because the database "
                "connection is unavailable."
            )

        # -------------------------------------------------------------------
        # Close database connection
        # -------------------------------------------------------------------

        _close_connection(conn)

        logger.info(
            "Database connection closed."
        )

    logger.info(
        "Run complete: status=%s records_written=%d",
        status,
        total_written,
    )

    # Treat partial failures as failures so GitHub Actions cannot
    # report a green run when ingestion actually failed.
    return 0 if status == "success" else 1


# ---------------------------------------------------------------------------
# Database writer
# ---------------------------------------------------------------------------


def _write_records(
    conn,
    records: list[ParsedEntity],
) -> int:
    """
    Delete raw events outside the retention window, then write the
    current feed records using PostgreSQL's execute_values bulk insert.

    Returns:
        Number of records written.
    """

    if not records:
        logger.info(
            "No records to write."
        )
        return 0

    # -----------------------------------------------------------------------
    # Retention cleanup
    # -----------------------------------------------------------------------

    logger.info(
        "Running raw event retention cleanup: keeping %d days.",
        RAW_EVENT_RETENTION_DAYS,
    )

    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                DELETE FROM raw_feed_event
                WHERE ingested_at < NOW() - (%s * INTERVAL '1 day')
                """,
                (RAW_EVENT_RETENTION_DAYS,),
            )

            deleted = cur.rowcount

        conn.commit()

        if deleted:
            logger.info(
                "Retention cleanup deleted %d raw events older than %d days.",
                deleted,
                RAW_EVENT_RETENTION_DAYS,
            )
        else:
            logger.info(
                "Retention cleanup deleted no rows."
            )

    except Exception:
        if not conn.closed:
            try:
                conn.rollback()
            except Exception:
                logger.exception(
                    "Database rollback failed after retention cleanup error."
                )

        raise

    # -----------------------------------------------------------------------
    # Prepare rows
    # -----------------------------------------------------------------------

    rows = [
        (
            record.entity_type,
            record.trip_id,
            record.trip_start_date,
            record.direction_id,
            record.route_id,
            record.stop_id,
            record.arrival_time,
            record.departure_time,
            record.vehicle_lat,
            record.vehicle_lon,
        )
        for record in records
    ]

    logger.info(
        "Writing %d records to PostgreSQL using bulk insert...",
        len(rows),
    )

    sql = """
        INSERT INTO raw_feed_event (
            entity_type,
            trip_id,
            trip_start_date,
            direction_id,
            route_id,
            stop_id,
            arrival_time,
            departure_time,
            vehicle_lat,
            vehicle_lon
        )
        VALUES %s
    """

    write_started = time.monotonic()

    try:
        with conn.cursor() as cur:
            execute_values(
                cur,
                sql,
                rows,
                page_size=1000,
            )

        conn.commit()

    except Exception:
        if not conn.closed:
            try:
                conn.rollback()
            except Exception:
                logger.exception(
                    "Database rollback failed after write error."
                )

        raise

    elapsed = time.monotonic() - write_started

    logger.info(
        "PostgreSQL bulk write committed: %d records in %.2fs.",
        len(rows),
        elapsed,
    )

    return len(rows)


# ---------------------------------------------------------------------------
# Ingestion run log
# ---------------------------------------------------------------------------


def _log_run(
    conn,
    started_at: datetime,
    status: str,
    records_written: int,
    error_message: str | None,
) -> None:
    """
    Record the outcome of the ingestion workflow.
    """

    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO ingestion_run_log (
                    started_at,
                    finished_at,
                    status,
                    records_written,
                    error_message
                )
                VALUES (
                    %s,
                    %s,
                    %s,
                    %s,
                    %s
                )
                """,
                (
                    started_at,
                    datetime.now(timezone.utc),
                    status,
                    records_written,
                    error_message,
                ),
            )

        conn.commit()

        logger.info(
            "Ingestion run log written: status=%s records=%d",
            status,
            records_written,
        )

    except Exception:
        logger.exception(
            "Failed to write ingestion_run_log entry."
        )

        if not conn.closed:
            try:
                conn.rollback()
            except Exception:
                logger.exception(
                    "Rollback after ingestion_run_log failure failed."
                )


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


if __name__ == "__main__":
    sys.exit(run())
