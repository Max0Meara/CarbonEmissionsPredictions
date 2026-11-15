"""Join the raw EIA and weather files into one hourly table.

Output: data/processed/hourly.csv, one row per UTC hour, with
  - generation by fuel and computed carbon intensity (gCO2/kWh)
  - demand, day-ahead demand forecast, net generation, net interchange
  - demand-weighted New England weather

Columns: 

period_utc - The hour this row covers, in UTC (6-7 pm EDT)
gen_NG - Natural gas generation in MWh that hour
gen_NUC - Nuclear generation
gen_SUN - Solar generation
gen_WAT - Hydro inside New England generation
gen_OTH - Other: wood, trash-to-energy, etc
gen_PS - Pumped storage hydro (negative when pumping)
gen_BAT - Battery storage, discharging (negative when charging)
gen_WND - Wind generation
gen_OIL - Oil generation
gen_SNB - Solar with integrated battery storage 
gen_COL - Coal
net_generation - Total generation inside New England (sum the gen variables)
demand - How much electricity New England actually used (per sub region but we sum it)
demand_forecast - ISO-NEs day-ahead prediction of demand
net_interchange - Net flow with neighbors (Negative = importing)
carbon_intensity - gCO2 per kWh generated this hour
ne_temperature_2m - Demand weighted New England temperature (Celcius) [a temperature metric adjusted so that regions or weather stations with higher energy consumption or higher population get more weight than sparsely populated or low-energy areas]
ne_wind_speed_100m - Wind at 100 m height (km/h)
ne_shortwave_radiation - Sunlight reaching the ground (W/m2)
ne_cloud_cover - Percent of sky covered

           
Ex Row: 2025-07-15 22:00+00:00, 9000, 3350, 800, 550, 450, 300, 150, 120, 20, 5, 0, 14745, 17200, 17050, -2455, 270.0, 29.5, 14.0, 310, 35 
"""
from pathlib import Path
import pandas as pd
RAW, OUT = Path("data/raw"), Path("data/processed")

# Emission factors in gCO2 per kWh generated. Zero for non-emitting fuels.
EMISSION_FACTORS = {"COL": 820, "NG": 490, "OIL": 740}
# TODO put this info in the README with siting information
# Coal - 820 gCO2 per kWh generated
# Natural Gas - 490 gCO2 per kWh generated
# Oil- 740 gCO2 per kWh generated
# According to https://world-nuclear.org/information-library/energy-and-the-environment/carbon-dioxide-emissions-from-electricity

# EIA subregion name keywords -> weather file zone name from EIA
ZONE_KEYWORDS = {
    "maine": "maine",
    "new hampshire": "new_hampshire",
    "vermont": "vermont",
    "connecticut": "connecticut",
    "rhode island": "rhode_island",
    "northeast": "northeast_ma",
    "southeast": "southeast_ma",
    "western": "west_central_ma",
}


def load_eia(name: str, column: str) -> pd.DataFrame:
    """Load one raw EIA file and pivot to wide format: index=UTC hour.
    Fuel-type data becomes gen_NG, gen_NUC, gen_WAT, and so on.
    Region data becomes demand, demand_forecast, net_generation, and net_interchange - renamed so it does not conflict with NG (Natural Gas)
    Subregion data becomes demand per load zone.
    """
    df = pd.read_csv(RAW / f"{name}.csv")
    df["period"] = pd.to_datetime(df["period"], format="%Y-%m-%dT%H", utc=True)
    df["value"] = pd.to_numeric(df["value"], errors="coerce")
    return df.pivot_table(index="period", columns=column, values="value", aggfunc="sum")


def carbon_intensity(fuel: pd.DataFrame) -> pd.Series:
    """ Calculates average carbon intensity (gCO2/kWh) = sum(gen * EF) / sum(gen).
    Only coal, gas, and oil have emission factors. Everything else counts as zero-emission.
    Negative generation (storage charging) is clipped to 0.
    """
    gen = fuel.clip(lower=0)
    emissions = sum(gen[f] * ef for f, ef in EMISSION_FACTORS.items() if f in gen)
    return emissions / gen.sum(axis=1)


def weighted_weather(subregion: pd.DataFrame) -> pd.DataFrame:
    """The weather that matters for grid demand is the weather where people use electricity.
    
    Average each weather variable across zones, weighted by zone demand share.
    Each EIA subregion is matched to its weather city by keyword. Every hour, each zone's share of total demand becomes its weight, so Boston counts for more than Burlington.
    Each hour, every zone's weight is its share of that hour's total New England demand, so they shift a little by season and time of day. On average, though, the ordering is stable.

    Ex:
    Connecticut              0.233
    Northeast Mass.          0.205
    Western/Central Mass.    0.137
    Southeast Mass.          0.121
    New Hampshire            0.099
    Maine                    0.096
    Rhode Island             0.067
    Vermont                  0.042

    BUT:
    It's the wrong weighting for wind and solar, because those drive supply. Wind farms are mostly in Maine and offshore, and Vermont and Maine have relatively more generation per person.
    """

    # TODO put info on solar and wind disparity in the readme
    zone_of = {}
    for col in subregion.columns:
        match = [z for k, z in ZONE_KEYWORDS.items() if k in str(col).lower()]
        if len(match) != 1:
            raise ValueError(f"Can't match EIA subregion {col!r} to a zone; edit ZONE_KEYWORDS")
        zone_of[col] = match[0]
    shares = subregion.div(subregion.sum(axis=1), axis=0).rename(columns=zone_of)

    frames = {}
    for zone in shares.columns:
        w = pd.read_csv(RAW / f"weather_{zone}.csv")
        w["time"] = pd.to_datetime(w["time"], utc=True)
        frames[zone] = w.set_index("time")

    variables = frames[next(iter(frames))].columns
    out = {}
    for var in variables:
        per_zone = pd.DataFrame({z: f[var] for z, f in frames.items()}) # hours × 8 cities
        per_zone = per_zone.reindex(shares.index)
        out[f"ne_{var}"] = (per_zone * shares[per_zone.columns]).sum(axis=1, min_count=1)
    return pd.DataFrame(out)


def main() -> None:
    fuel = load_eia("eia_fuel_type", "fueltype").add_prefix("gen_") # load the data!
    fuel = fuel.fillna(0) # fill gaps in the data with 0 
    region = load_eia("eia_region", "type").rename(  # avoid clash with fuel 'NG'
        columns={"D": "demand", "DF": "demand_forecast", "NG": "net_generation", "TI": "net_interchange"}
    )
    subregion = load_eia("eia_subregion", "subba-name")  # demand by zone

    df = fuel.join(region, how="outer")
    df["carbon_intensity"] = carbon_intensity(fuel.rename(columns=lambda c: c[4:]))
    # Flag hours where fuel generation disagrees with reported net generation
    gen_total = fuel.clip(lower=0).sum(axis=1)
    mismatch = ((gen_total - df["net_generation"]) / df["net_generation"]).abs() > 0.05
    df.loc[mismatch, "carbon_intensity"] = float("nan")
    print(f"flagged {mismatch.sum()} hours where fuel totals disagree with net generation by >5%")
    df = df.join(weighted_weather(subregion), how="left")

    # Reindex to a complete hourly range so missing hours become visible NaNs
    full = pd.date_range(df.index.min(), df.index.max(), freq="h", tz="UTC")
    missing_hours = len(full) - len(df)
    df = df.reindex(full).rename_axis("period_utc")
    # report gaps in the data

    OUT.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT / "hourly.csv")

    print(f"saved {len(df):,} hours x {df.shape[1]} columns -> {OUT / 'hourly.csv'}")
    print(f"hours absent from EIA entirely: {missing_hours}")
    print("missing values per column:")
    print(df.isna().sum()[lambda s: s > 0].to_string() or "  none")
    print(df.groupby(df.index.hour)["demand"].mean().idxmax(), "UTC is the peak hour")


if __name__ == "__main__":
    main()
