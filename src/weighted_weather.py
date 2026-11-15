import pandas as pd
sub = pd.read_csv("data/raw/eia_subregion.csv")
avg = sub.groupby("subba-name")["value"].sum()
print((avg / avg.sum()).sort_values(ascending=False).round(3))