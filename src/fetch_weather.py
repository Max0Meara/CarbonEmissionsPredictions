import time
from pathlib import Path
import pandas as pd
import requests

URL = "https://archive-api.open-meteo.com/v1/archive"
START, END = "2023-01-01", "2025-12-31" # time range
VARS = ["temperature_2m", "wind_speed_100m", "shortwave_radiation", "cloud_cover"]
OUT = Path("data/raw")
# TODO update readme with update data sources

# One representative city per ISO-NE load zone
# Keys are keywords matched against EIA's subregion names in build_dataset.py
ZONES = {
    "maine": (43.66, -70.26), # Portland
    "new_hampshire": (42.99, -71.46), # Manchester
    "vermont": (44.48, -73.21), # Burlington
    "connecticut": (41.76, -72.68), # Hartford
    "rhode_island": (41.82, -71.41), # Providence
    "northeast_ma": (42.36, -71.06), # Boston!
    "southeast_ma": (42.08, -71.02), # Brockton
    "west_central_ma": (42.26, -71.80), # Worcester
}


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    for zone, (lat, lon) in ZONES.items():
        path = OUT / f"weather_{zone}.csv"
        if path.exists():
            print(f"skip {path} (already downloaded)")
            continue
        params = {
            "latitude": lat,
            "longitude": lon,
            "start_date": START,
            "end_date": END,
            "hourly": ",".join(VARS),
            "timezone": "UTC",  # match EIA's UTC periods
        }
        r = requests.get(URL, params=params, timeout=120)
        r.raise_for_status()
        df = pd.DataFrame(r.json()["hourly"])
        df.to_csv(path, index=False)
        print(f"saved {len(df):,} rows -> {path}")
        time.sleep(1)  # staying under Open Meteo's free tier rate limit


if __name__ == "__main__":
    main()
