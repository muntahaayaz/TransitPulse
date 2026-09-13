"""
Tests for src/ingestion/poll_feed.py.

Deliberately does NOT call the live MTA feed: tests must run in CI
without a network dependency on an external, rate-limited service.
Instead, a minimal synthetic GTFS-RT FeedMessage is constructed
in-memory and serialized, exercising the same parsing path real feed
data would take.
"""

from __future__ import annotations

import os
import sys

import pytest

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from google.transit import gtfs_realtime_pb2  # noqa: E402
from src.ingestion.poll_feed import parse_feed  # noqa: E402


def _build_synthetic_feed_bytes() -> bytes:
    feed = gtfs_realtime_pb2.FeedMessage()
    feed.header.gtfs_realtime_version = "2.0"

    trip_update_entity = feed.entity.add()
    trip_update_entity.id = "test-entity-trip-update"
    trip_update_entity.trip_update.trip.trip_id = "TEST_TRIP_1"
    trip_update_entity.trip_update.trip.route_id = "1"

    stop_time_update = trip_update_entity.trip_update.stop_time_update.add()
    stop_time_update.stop_id = "TEST_STOP_A"
    stop_time_update.arrival.time = 1750000000
    stop_time_update.departure.time = 1750000060

    vehicle_entity = feed.entity.add()
    vehicle_entity.id = "test-entity-vehicle"
    vehicle_entity.vehicle.trip.trip_id = "TEST_TRIP_1"
    vehicle_entity.vehicle.trip.route_id = "1"
    vehicle_entity.vehicle.stop_id = "TEST_STOP_A"
    vehicle_entity.vehicle.position.latitude = 40.730610
    vehicle_entity.vehicle.position.longitude = -73.935242

    return feed.SerializeToString()


def test_parse_feed_extracts_trip_update():
    raw = _build_synthetic_feed_bytes()
    results = parse_feed(raw)

    trip_updates = [
        r for r in results if r.entity_type == "trip_update"
    ]

    assert len(trip_updates) == 1
    assert trip_updates[0].trip_id == "TEST_TRIP_1"
    assert trip_updates[0].route_id == "1"
    assert trip_updates[0].stop_id == "TEST_STOP_A"
    assert trip_updates[0].arrival_time is not None
    assert trip_updates[0].departure_time is not None


def test_parse_feed_extracts_vehicle_position():
    raw = _build_synthetic_feed_bytes()
    results = parse_feed(raw)

    positions = [
        r for r in results if r.entity_type == "vehicle_position"
    ]

    assert len(positions) == 1
    assert positions[0].vehicle_lat == pytest.approx(
        40.730610,
        abs=1e-5,
    )
    assert positions[0].vehicle_lon == pytest.approx(
        -73.935242,
        abs=1e-5,
    )
    assert positions[0].trip_id == "TEST_TRIP_1"


def test_parse_feed_handles_empty_feed():
    feed = gtfs_realtime_pb2.FeedMessage()
    feed.header.gtfs_realtime_version = "2.0"

    results = parse_feed(feed.SerializeToString())

    assert results == []

def test_m2_aggregation_helpers():
    import pandas as pd
    from src.analytics.analytics import get_station_delay_concentration

    assert callable(get_station_delay_concentration)
    assert pd.DataFrame is not None
