-- M0 (Walking Skeleton) schema.
--
-- Deliberately minimal: one raw fact table, no dimension tables yet.
-- Dimension tables (route/stop/trip/calendar from static GTFS) and the
-- real on-time/delay computation arrive in M1 -- see ROADMAP.md.
--
-- Apply with: psql "$DATABASE_URL" -f src/db/schema.sql
-- (Safe to re-run: all statements are idempotent.)

CREATE TABLE IF NOT EXISTS raw_feed_event (
    id              BIGSERIAL PRIMARY KEY,
    ingested_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
    entity_type     TEXT NOT NULL CHECK (entity_type IN ('trip_update', 'vehicle_position')),
    trip_id         TEXT,
    route_id        TEXT,
    stop_id         TEXT,
    arrival_time    TIMESTAMPTZ,
    departure_time  TIMESTAMPTZ,
    vehicle_lat     DOUBLE PRECISION,
    vehicle_lon     DOUBLE PRECISION
);

CREATE INDEX IF NOT EXISTS idx_raw_feed_event_route_id     ON raw_feed_event (route_id);
CREATE INDEX IF NOT EXISTS idx_raw_feed_event_ingested_at  ON raw_feed_event (ingested_at);

-- Ingestion run log -- satisfies FR-10 / NFR-1 / NFR-8 (see ARCHITECTURE.md
-- Section 2.1). One row per ingestion workflow run, so pipeline health is
-- queryable from the same system the dashboard already reads from.
CREATE TABLE IF NOT EXISTS ingestion_run_log (
    id                BIGSERIAL PRIMARY KEY,
    started_at        TIMESTAMPTZ NOT NULL,
    finished_at       TIMESTAMPTZ,
    status            TEXT NOT NULL CHECK (status IN ('success', 'partial_failure', 'failure')),
    records_written   INT NOT NULL DEFAULT 0,
    error_message     TEXT
);

CREATE INDEX IF NOT EXISTS idx_ingestion_run_log_started_at ON ingestion_run_log (started_at);
