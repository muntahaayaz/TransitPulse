"""
TransitPulse GTFS-Realtime feed client.

Fetches and parses the MTA NYC Subway GTFS-Realtime feed.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional

import requests
from google.transit import gtfs_realtime_pb2


DEFAULT_FEED_URL = (
    "https://api-endpoint.mta.info/"
    "Dataservice/mtagtfsfeeds/nyct%2Fgtfs"
)


@dataclass
class ParsedEntity:
    """Normalized GTFS-Realtime observation."""

    trip_id: Optional[str]
    trip_start_date: Optional[str]
    direction_id: Optional[str]
    route_id: Optional[str]
    stop_id: Optional[str]
    arrival_time: Optional[datetime]
    departure_time: Optional[datetime]
    vehicle_lat: Optional[float]
    vehicle_lon: Optional[float]
    entity_type: str


def fetch_feed(
    feed_url: Optional[str] = None,
    timeout_seconds: int = 15,
) -> bytes:
    """Fetch the raw GTFS-Realtime protobuf feed."""

    url = (
        feed_url
        or os.environ.get("GTFS_FEED_URL")
        or DEFAULT_FEED_URL
    )

    response = requests.get(
        url,
        timeout=timeout_seconds,
    )

    response.raise_for_status()

    return response.content


def parse_feed(raw_bytes: bytes) -> list[ParsedEntity]:
    """Parse GTFS-Realtime protobuf bytes into normalized records."""

    feed = gtfs_realtime_pb2.FeedMessage()
    feed.ParseFromString(raw_bytes)

    results: list[ParsedEntity] = []

    for entity in feed.entity:

        if entity.HasField("trip_update"):

            trip_update = entity.trip_update

            trip_id = trip_update.trip.trip_id or None
            trip_start_date = trip_update.trip.start_date or None
            direction_id = None

            if trip_id:
                if "..N" in trip_id:
                    direction_id = "0"
                elif "..S" in trip_id:
                    direction_id = "1"
            route_id = trip_update.trip.route_id or None

            for stop_time_update in trip_update.stop_time_update:

                arrival = None
                departure = None

                if stop_time_update.HasField("arrival"):
                    arrival = _to_datetime(
                        stop_time_update.arrival.time
                    )

                if stop_time_update.HasField("departure"):
                    departure = _to_datetime(
                        stop_time_update.departure.time
                    )

                results.append(
                    ParsedEntity(
                        trip_id=trip_id,
                        trip_start_date=trip_start_date,
                        direction_id=direction_id,
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

            vehicle = entity.vehicle

            trip_id = vehicle.trip.trip_id or None
            route_id = vehicle.trip.route_id or None
            stop_id = vehicle.stop_id or None

            latitude = None
            longitude = None

            if vehicle.HasField("position"):
                latitude = vehicle.position.latitude
                longitude = vehicle.position.longitude

            results.append(
                ParsedEntity(
                    trip_id=trip_id,
                    trip_start_date=None,
                    direction_id=None,
                    route_id=route_id,
                    stop_id=stop_id,
                    arrival_time=None,
                    departure_time=None,
                    vehicle_lat=latitude,
                    vehicle_lon=longitude,
                    entity_type="vehicle_position",
                )
            )

    return results


def _to_datetime(
    epoch_seconds: int,
) -> Optional[datetime]:
    """Convert Unix epoch seconds to UTC datetime."""

    if not epoch_seconds:
        return None

    return datetime.fromtimestamp(
        epoch_seconds,
        tz=timezone.utc,
    )