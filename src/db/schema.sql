-- TransitPulse database schema.
--
-- Raw real-time observations + static GTFS reference data.
--
-- Safe to re-run: all statements are idempotent.

-- ---------------------------------------------------------------------------
-- Raw GTFS-Realtime observations
-- ---------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS raw_feed_event (
    id              BIGSERIAL PRIMARY KEY,
    ingested_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
    entity_type     TEXT NOT NULL CHECK (
        entity_type IN ('trip_update', 'vehicle_position')
    ),
    trip_id         TEXT,
    route_id        TEXT,
    stop_id         TEXT,
    arrival_time    TIMESTAMPTZ,
    departure_time  TIMESTAMPTZ,
    vehicle_lat     DOUBLE PRECISION,
    vehicle_lon     DOUBLE PRECISION
);

CREATE INDEX IF NOT EXISTS idx_raw_feed_event_route_id
    ON raw_feed_event (route_id);

CREATE INDEX IF NOT EXISTS idx_raw_feed_event_stop_id
    ON raw_feed_event (stop_id);

CREATE INDEX IF NOT EXISTS idx_raw_feed_event_trip_id
    ON raw_feed_event (trip_id);

CREATE INDEX IF NOT EXISTS idx_raw_feed_event_ingested_at
    ON raw_feed_event (ingested_at);


-- ---------------------------------------------------------------------------
-- Ingestion run log
-- ---------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS ingestion_run_log (
    id              BIGSERIAL PRIMARY KEY,
    started_at      TIMESTAMPTZ NOT NULL,
    finished_at     TIMESTAMPTZ,
    status          TEXT NOT NULL CHECK (
        status IN ('success', 'partial_failure', 'failure')
    ),
    records_written INT NOT NULL DEFAULT 0,
    error_message   TEXT
);

CREATE INDEX IF NOT EXISTS idx_ingestion_run_log_started_at
    ON ingestion_run_log (started_at);


-- ---------------------------------------------------------------------------
-- Static GTFS routes
-- ---------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS gtfs_routes (
    route_id          TEXT PRIMARY KEY,
    agency_id         TEXT,
    route_short_name  TEXT,
    route_long_name   TEXT,
    route_type        INT
);


-- ---------------------------------------------------------------------------
-- Static GTFS stops
-- ---------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS gtfs_stops (
    stop_id    TEXT PRIMARY KEY,
    stop_name  TEXT,
    stop_lat   DOUBLE PRECISION,
    stop_lon   DOUBLE PRECISION
);

CREATE INDEX IF NOT EXISTS idx_gtfs_stops_name
    ON gtfs_stops (stop_name);


-- ---------------------------------------------------------------------------
-- Static GTFS trips
-- ---------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS gtfs_trips (
    trip_id         TEXT PRIMARY KEY,
    route_id        TEXT,
    service_id      TEXT,
    trip_headsign   TEXT,
    direction_id    TEXT,
    shape_id        TEXT
);

CREATE INDEX IF NOT EXISTS idx_gtfs_trips_route_id
    ON gtfs_trips (route_id);

CREATE INDEX IF NOT EXISTS idx_gtfs_trips_service_id
    ON gtfs_trips (service_id);


-- ---------------------------------------------------------------------------
-- Static GTFS stop times
-- ---------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS gtfs_stop_times (
    trip_id         TEXT NOT NULL,
    stop_id         TEXT NOT NULL,
    stop_sequence   INT NOT NULL,
    arrival_time    TEXT,
    departure_time  TEXT,

    PRIMARY KEY (trip_id, stop_sequence)
);

CREATE INDEX IF NOT EXISTS idx_gtfs_stop_times_stop_id
    ON gtfs_stop_times (stop_id);

CREATE INDEX IF NOT EXISTS idx_gtfs_stop_times_trip_id
    ON gtfs_stop_times (trip_id);


-- ---------------------------------------------------------------------------
-- Static GTFS service calendar
-- ---------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS gtfs_calendar (
    service_id  TEXT PRIMARY KEY,
    monday      INT,
    tuesday     INT,
    wednesday   INT,
    thursday    INT,
    friday      INT,
    saturday    INT,
    sunday      INT,
    start_date  TEXT,
    end_date    TEXT
);


-- ---------------------------------------------------------------------------
-- Static GTFS calendar exceptions
-- ---------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS gtfs_calendar_dates (
    service_id     TEXT NOT NULL,
    date           TEXT NOT NULL,
    exception_type INT NOT NULL,

    PRIMARY KEY (service_id, date)
);
