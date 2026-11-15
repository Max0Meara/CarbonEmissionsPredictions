import os
import sys
import time
from pathlib import Path
import pandas as pd
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

BASE = "https://api.eia.gov/v2/electricity/rto"
START, END = "2023-01-01", "2025-12-31"  # 'hourly' period time range in UTC
PAGE = 5000  # EIA free range
TIMEOUT = 120
RAW = Path("data/raw")
CHUNKS = RAW / "eia_chunks"

# name -> (API route, facets, secondary sort column)
DATASETS = {
    "eia_fuel_type": ("fuel-type-data", {"facets[respondent][]": "ISNE"}, "fueltype"),
    "eia_region": ("region-data", {"facets[respondent][]": "ISNE"}, "type"),
    "eia_subregion": ("region-sub-ba-data", {"facets[parent][]": "ISNE"}, "subba"),
    "eia_interchange": ("interchange-data", {"facets[fromba][]": "ISNE"}, "toba"),
}


def make_session() -> requests.Session:
    retry = Retry(
        total=6,
        connect=6,
        read=6,
        backoff_factor=2,  # waits 2 seconds between attempts
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET"],
    )
    s = requests.Session()
    s.mount("https://", HTTPAdapter(max_retries=retry))
    return s


def months(start: str, end: str):
    # sort by month
    for m in pd.date_range(start, end, freq="MS"):
        last = m + pd.offsets.MonthEnd(0)
        yield m.strftime("%Y-%m-%dT00"), last.strftime("%Y-%m-%dT23"), m.strftime("%Y-%m")


def fetch_window(session, route, facets, tiebreak, key, start, end) -> pd.DataFrame:
    rows, offset = [], 0
    while True:
        params = {
            "api_key": key,
            "frequency": "hourly",
            "data[0]": "value",
            "start": start,
            "end": end,
            "sort[0][column]": "period",
            "sort[0][direction]": "asc",
            "sort[1][column]": tiebreak,
            "sort[1][direction]": "asc",
            "offset": offset,
            "length": PAGE,
            **facets,
        }
        r = session.get(f"{BASE}/{route}/data/", params=params, timeout=TIMEOUT)
        r.raise_for_status()
        resp = r.json()["response"]
        batch = resp["data"]
        rows.extend(batch)
        offset += len(batch)
        if not batch or offset >= int(resp["total"]):
            return pd.DataFrame(rows)
        time.sleep(0.25)  # dont spam the api


def main() -> None:
    key = os.environ.get("EIA_API_KEY")
    if not key:
        sys.exit("EIA_API_KEY is not set. Add it to .env (see .env.example).")
    session = make_session()

    for name, (route, facets, tiebreak) in DATASETS.items():
        final = RAW / f"{name}.csv"
        if final.exists():
            print(f"skip {final} (already downloaded)")
            continue
        chunk_dir = CHUNKS / name
        chunk_dir.mkdir(parents=True, exist_ok=True)
        print(f"fetching {name}")
        for start, end, label in months(START, END):
            path = chunk_dir / f"{label}.csv"
            if path.exists():
                continue
            df = fetch_window(session, route, facets, tiebreak, key, start, end)
            df.to_csv(path, index=False)
            print(f"  {label}: {len(df):,} rows")

        combined = pd.concat(
            [pd.read_csv(p) for p in sorted(chunk_dir.glob("*.csv"))], ignore_index=True
        ).drop_duplicates()
        combined.to_csv(final, index=False)
        print(f"  saved {len(combined):,} rows -> {final}")


if __name__ == "__main__":
    main()