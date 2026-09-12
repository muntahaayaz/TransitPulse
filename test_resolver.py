from src.db.connection import get_connection
import pandas as pd
from src.analytics.reliability import resolve_realtime_event

c = get_connection()

q = """
SELECT
    route_id,
    direction_id,
    trip_start_date,
    stop_id,
    COALESCE(departure_time, arrival_time) AS actual_time
FROM raw_feed_event
WHERE route_id IS NOT NULL
  AND direction_id IS NOT NULL
  AND trip_start_date IS NOT NULL
  AND stop_id IS NOT NULL
  AND (arrival_time IS NOT NULL OR departure_time IS NOT NULL)
ORDER BY ingested_at DESC
LIMIT 50;
"""

df = pd.read_sql(q, c)

matched = 0
unmatched = 0
distances = []
delays = []

print("Testing", len(df), "events...")
print()

for _, r in df.iterrows():
    result = resolve_realtime_event(
        c,
        str(r.route_id),
        str(r.direction_id),
        str(r.trip_start_date),
        str(r.stop_id),
        r.actual_time,
    )

    if result:
        matched += 1
        distances.append(result["match_distance_minutes"])
        delays.append(result["delay_minutes"])
    else:
        unmatched += 1

print()
print("===== RESULTS =====")
print("MATCHED:", matched)
print("UNMATCHED:", unmatched)
print("TOTAL:", len(df))

if len(df) > 0:
    print("MATCH RATE:", round(matched / len(df) * 100, 2), "%")

if distances:
    print(
        "AVG MATCH DISTANCE:",
        round(sum(distances) / len(distances), 2),
        "minutes",
    )

if delays:
    print(
        "AVG DELAY:",
        round(sum(delays) / len(delays), 2),
        "minutes",
    )
