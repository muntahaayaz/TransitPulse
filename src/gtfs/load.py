"""
TransitPulse GTFS static-data loader.

Loads the MTA NYC Subway GTFS static feed into PostgreSQL reference tables.
"""

from __future__ import annotations

import csv
from pathlib import Path

from psycopg2.extras import execute_values

from src.db.connection import get_connection


def _read_csv(path: Path) -> list[dict[str, str]]:
    """Read a GTFS CSV file into dictionaries."""
    with path.open(
        "r",
        encoding="utf-8-sig",
        newline="",
    ) as file:
        return list(csv.DictReader(file))


def _to_int(value: str | None) -> int | None:
    """Convert a GTFS integer field safely."""
    if value in (None, ""):
        return None

    return int(value)


def _to_float(value: str | None) -> float | None:
    """Convert a GTFS floating-point field safely."""
    if value in (None, ""):
        return None

    return float(value)


def load_gtfs(gtfs_dir: str | Path = "data/gtfs") -> None:
    """
    Load the static GTFS reference data into PostgreSQL.

    Tables loaded:
        gtfs_routes
        gtfs_stops
        gtfs_trips
        gtfs_stop_times
        gtfs_calendar
        gtfs_calendar_dates
    """

    gtfs_path = Path(gtfs_dir)

    routes = _read_csv(gtfs_path / "routes.txt")
    stops = _read_csv(gtfs_path / "stops.txt")
    trips = _read_csv(gtfs_path / "trips.txt")
    stop_times = _read_csv(gtfs_path / "stop_times.txt")
    calendar = _read_csv(gtfs_path / "calendar.txt")
    calendar_dates = _read_csv(gtfs_path / "calendar_dates.txt")

    conn = get_connection()

    try:
        with conn.cursor() as cur:

            # Clear existing static reference data.
            cur.execute(
                """
                TRUNCATE TABLE
                    gtfs_stop_times,
                    gtfs_trips,
                    gtfs_calendar_dates,
                    gtfs_calendar,
                    gtfs_routes,
                    gtfs_stops;
                """
            )

            # Routes
            route_rows = [
                (
                    row.get("route_id"),
                    row.get("agency_id"),
                    row.get("route_short_name"),
                    row.get("route_long_name"),
                    _to_int(row.get("route_type")),
                )
                for row in routes
            ]

            execute_values(
                cur,
                """
                INSERT INTO gtfs_routes (
                    route_id,
                    agency_id,
                    route_short_name,
                    route_long_name,
                    route_type
                )
                VALUES %s
                """,
                route_rows,
                page_size=1000,
            )

            # Stops
            stop_rows = [
                (
                    row.get("stop_id"),
                    row.get("stop_name"),
                    _to_float(row.get("stop_lat")),
                    _to_float(row.get("stop_lon")),
                )
                for row in stops
            ]

            execute_values(
                cur,
                """
                INSERT INTO gtfs_stops (
                    stop_id,
                    stop_name,
                    stop_lat,
                    stop_lon
                )
                VALUES %s
                """,
                stop_rows,
                page_size=1000,
            )

            # Trips
            trip_rows = [
                (
                    row.get("trip_id"),
                    row.get("route_id"),
                    row.get("service_id"),
                    row.get("trip_headsign"),
                    row.get("direction_id"),
                    row.get("shape_id"),
                )
                for row in trips
            ]

            execute_values(
                cur,
                """
                INSERT INTO gtfs_trips (
                    trip_id,
                    route_id,
                    service_id,
                    trip_headsign,
                    direction_id,
                    shape_id
                )
                VALUES %s
                """,
                trip_rows,
                page_size=1000,
            )

            # Stop times
            stop_time_rows = [
                (
                    row.get("trip_id"),
                    row.get("stop_id"),
                    _to_int(row.get("stop_sequence")),
                    row.get("arrival_time") or None,
                    row.get("departure_time") or None,
                )
                for row in stop_times
            ]

            execute_values(
                cur,
                """
                INSERT INTO gtfs_stop_times (
                    trip_id,
                    stop_id,
                    stop_sequence,
                    arrival_time,
                    departure_time
                )
                VALUES %s
                """,
                stop_time_rows,
                page_size=5000,
            )

            # Calendar
            calendar_rows = [
                (
                    row.get("service_id"),
                    _to_int(row.get("monday")),
                    _to_int(row.get("tuesday")),
                    _to_int(row.get("wednesday")),
                    _to_int(row.get("thursday")),
                    _to_int(row.get("friday")),
                    _to_int(row.get("saturday")),
                    _to_int(row.get("sunday")),
                    row.get("start_date"),
                    row.get("end_date"),
                )
                for row in calendar
            ]

            execute_values(
                cur,
                """
                INSERT INTO gtfs_calendar (
                    service_id,
                    monday,
                    tuesday,
                    wednesday,
                    thursday,
                    friday,
                    saturday,
                    sunday,
                    start_date,
                    end_date
                )
                VALUES %s
                """,
                calendar_rows,
                page_size=1000,
            )

            # Calendar exceptions
            calendar_date_rows = [
                (
                    row.get("service_id"),
                    row.get("date"),
                    _to_int(row.get("exception_type")),
                )
                for row in calendar_dates
            ]

            execute_values(
                cur,
                """
                INSERT INTO gtfs_calendar_dates (
                    service_id,
                    date,
                    exception_type
                )
                VALUES %s
                """,
                calendar_date_rows,
                page_size=1000,
            )

        conn.commit()

    except Exception:
        conn.rollback()
        raise

    finally:
        conn.close()


if __name__ == "__main__":
    load_gtfs()
    print("GTFS static data loaded successfully.")
