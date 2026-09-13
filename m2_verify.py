from src.db.connection import get_connection
from src.analytics.reliability import get_reliability_observations

c = get_connection()
obs = get_reliability_observations(c, limit=100)

print("OBSERVATIONS:", len(obs))

data = obs[obs["route_id"].isin(["1","2","3","4","5","6","7"])].dropna(subset=["delay_minutes"]).copy()

print("\n--- STATION DELAYS ---")
station = data.groupby(["route_id","stop_id"]).agg(
    observations=("delay_minutes","count"),
    average_delay_minutes=("delay_minutes","mean")
).query("observations >= 2").sort_values("average_delay_minutes", ascending=False).head(10)
print(station.round(2).to_string())

print("\n--- TIME WINDOWS ---")
data["hour"] = data["actual_time"].dt.hour
hourly = data.groupby("hour").agg(
    observations=("delay_minutes","count"),
    average_delay_minutes=("delay_minutes","mean")
).sort_index()
print(hourly.round(2).to_string())

print("\n=== M2 VERIFICATION COMPLETE ===")
