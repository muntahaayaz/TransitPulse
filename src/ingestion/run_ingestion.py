"""
M0 ingestion driver -- the entry point GitHub Actions invokes.

Implements the triggered/looped polling pattern chosen in ADR-001
(ARCHITECTURE.md Section 5): rather than a persistent long-running
process, this runs for a fixed duration, polling the feed repeatedly
within that window, then exits cleanly before the next scheduled trigger.

One row is written to ingestion_run_log per invocation regardless of
outcome, so pipeline health is queryable (FR-10, NFR-1, NFR-8) rather
than requiring a manual check of GitHub's own run history.
"""
from __future__ import annotations

import os
import sys
import time
import logging
from datetime import datetime, timezone

# Import strategy: this project uses absolute imports rooted at the
# project's top-level `src` package everywhere (see src/db/connection.py,
# src/dashboard/app.py, tests/). That works automatically when running
# `python -m src.ingestion.run_ingestion` from the project root, or when
# importing e.g. `from src.ingestion.run_ingestion import run` -- both
# put the project root on sys.path already. It does NOT work automatically
# for `python src/ingestion/run_ingestion.py` (direct script execution),
# because Python only puts this file's own directory on sys.path in that
# case, not the project root. This line closes that one gap, and is a
# no-op (append is idempotent enough for our purposes) when the project
# root is already on sys.path via another entry method.
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from src.ingestion.poll_feed import fetch_feed, parse_feed, ParsedEntity  # noqa: E402
from src.db.connection import get_connection  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

POLL_INTERVAL_SECONDS = int(os.environ.get("POLL_INTERVAL_SECONDS", "30"))
# Default run duration leaves margin before a 15-minute cron trigger,
# so consecutive runs don't overlap. See .github/workflows/ingest.yml.
RUN_DURATION_SECONDS = int(os.environ.get("RUN_DURATION_SECONDS", str(8 * 60)))


def run() -> int:
    """Run one ingestion cycle. Returns process exit code (0 success/partial, 1 total failure)."""
    started_at = datetime.now(timezone.utc)
    total_written = 0
    status = "success"
    error_message: str | None = None

    try:
        conn = get_connection()
    except Exception as exc:  # noqa: BLE001 -- can't even log to DB if this fails; must surface loudly
        logger.exception("Could not obtain a database connection; aborting run.")
        # No DB connection means we can't write to ingestion_run_log either --
        # this failure mode relies on GitHub Actions' own run history/exit code.
        return 1

    try:
        deadline = time.monotonic() + RUN_DURATION_SECONDS
        while time.monotonic() < deadline:
            cycle_start = time.monotonic()
            try:
                raw_bytes = fetch_feed()
                records = parse_feed(raw_bytes)
                total_written += _write_records(conn, records)
            except Exception as exc:  # noqa: BLE001 -- one bad poll must not kill the whole run
                logger.exception("Poll cycle failed: %s", exc)
                status = "partial_failure"
                error_message = str(exc)

            elapsed = time.monotonic() - cycle_start
            time.sleep(max(0, POLL_INTERVAL_SECONDS - elapsed))

    except Exception as exc:  # noqa: BLE001
        logger.exception("Ingestion run failed entirely: %s", exc)
        status = "failure"
        error_message = str(exc)
    finally:
        _log_run(conn, started_at, status, total_written, error_message)
        conn.close()

    logger.info("Run complete: status=%s records_written=%d", status, total_written)
    return 0 if status != "failure" else 1


def _write_records(conn, records: list[ParsedEntity]) -> int:
    if not records:
        return 0
    with conn.cursor() as cur:
        cur.executemany(
            """
            INSERT INTO raw_feed_event
                (entity_type, trip_id, route_id, stop_id, arrival_time, departure_time, vehicle_lat, vehicle_lon)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """,
            [
                (
                    r.entity_type,
                    r.trip_id,
                    r.route_id,
                    r.stop_id,
                    r.arrival_time,
                    r.departure_time,
                    r.vehicle_lat,
                    r.vehicle_lon,
                )
                for r in records
            ],
        )
    conn.commit()
    return len(records)


def _log_run(conn, started_at: datetime, status: str, records_written: int, error_message: str | None) -> None:
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO ingestion_run_log (started_at, finished_at, status, records_written, error_message)
                VALUES (%s, %s, %s, %s, %s)
                """,
                (started_at, datetime.now(timezone.utc), status, records_written, error_message),
            )
        conn.commit()
    except Exception:  # noqa: BLE001
        # Deliberately not re-raised: a logging failure shouldn't mask the
        # original run's success/failure status returned to the caller.
        logger.exception("Failed to write ingestion_run_log entry.")


if __name__ == "__main__":
    sys.exit(run())
