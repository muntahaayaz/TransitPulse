"""
Fetches and parses a single polling cycle of the MTA GTFS-Realtime feed
for the numbered lines (1/2/3/4/5/6/S).

Scope note (M0): only standard GTFS-Realtime fields are parsed (trip_id,
route_id, stop_id, arrival/departure times, vehicle position).
NYCT-specific protobuf extension fields (e.g. explicit train direction,
assigned/unassigned status) are NOT parsed yet. This is a deliberate M0
scope decision -- see ROADMAP.md M0 definition. If this is still true
after M1, it should be logged in TECH_DEBT.md.

Feed URL note: MTA's real-time feed endpoints have changed over time and
the key requirement was removed in 2024. Verify the current URL against
MTA's Developer Resources (https://www.mta.info/developers) before
relying on DEFAULT_FEED_URL below -- it is provided as a documented
starting point, not a guarantee, since this environment has no network
access to verify it live.
"""
from __future__ import annotations

import os
import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional

import requests
from google.transit import gtfs_realtime_pb2

logger = logging.getLogger(__name__)

DEFAULT_FEED_URL = "https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds/nyct%2Fgtfs"


@dataclass
class ParsedEntity:
    trip_id: Optional[str]
    route_id: Optional[str]
    stop_id: Optional[str]
    arrival_time: Optional[datetime]
    departure_time: Optional[datetime]
    vehicle_lat: Optional[float]
    vehicle_lon: Optional[float]
    entity_type: str  # "trip_update" or "vehicle_position"


def fetch_feed(feed_url: Optional[str] = None, timeout_seconds: int = 15) -> bytes:
    """Fetch raw protobuf bytes from the MTA GTFS-RT feed. Raises on HTTP error."""
    url = feed_url or os.environ.get("GTFS_FEED_URL", DEFAULT_FEED_URL)
    response = requests.get(url, timeout=timeout_seconds)
    response.raise_for_status()
    return response.content


def parse_feed(raw_bytes: bytes) -> list[ParsedEntity]:
    """Parse raw GTFS-RT protobuf bytes into a list of ParsedEntity records."""
    feed = gtfs_realtime_pb2.FeedMessage()
    feed.ParseFromString(raw_bytes)

    results: list[ParsedEntity] = []

    for entity in feed.entity:
        if entity.HasField("trip_update"):
            tu = entity.trip_update
            trip_id = tu.trip.trip_id or None
            route_id = tu.trip.route_id or None
            for stop_time_update in tu.stop_time_update:
                arrival = (
                    _to_datetime(stop_time_update.arrival.time)
                    if stop_time_update.HasField("arrival")
                    else None
                )
                departure = (
                    _to_datetime(stop_time_update.departure.time)
                    if stop_time_update.HasField("departure")
                    else None
                )
                results.append(
                    ParsedEntity(
                        trip_id=trip_id,
                        route_id=route_id,
                        stop_id=stop_time_update.stop_id or None,
                        arrival_time=arrival,
                        departure_time=departure,
                        vehicle_lat=None,
                        vehicle_lon=None,
                        entity_type="trip_update",
                    )
                )

        if entity.HasField("vehicle"):
            v = entity.vehicle
            results.append(
                ParsedEntity(
                    trip_id=v.trip.trip_id or None,
                    route_id=v.trip.route_id or None,
                    stop_id=v.stop_id or None,
                    arrival_time=None,
                    departure_time=None,
                    vehicle_lat=v.position.latitude if v.HasField("position") else None,
                    vehicle_lon=v.position.longitude if v.HasField("position") else None,
                    entity_type="vehicle_position",
                )
            )

    return results


def _to_datetime(epoch_seconds: int) -> Optional[datetime]:
    if not epoch_seconds:
        return None
    return datetime.fromtimestamp(epoch_seconds, tz=timezone.utc)
