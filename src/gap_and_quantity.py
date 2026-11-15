import pandas as pd
from pathlib import Path

script_dir = Path(__file__).resolve().parent
data_dir = script_dir.parent / "data"

df = pd.read_csv(f"{data_dir}/processed/hourly.csv", index_col=0)
gen = df.filter(like="gen_").clip(lower=0).sum(axis=1)
gap = (gen - df["net_generation"]) / df["net_generation"]
print("coal missing:", gap[df["gen_COL"].isna()].describe())
print("coal present:", gap[df["gen_COL"].notna()].describe())
bad = gap[gap.abs() > 0.05]
print(len(bad))
print(bad.sort_values().head(10))