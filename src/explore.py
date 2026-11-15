"""Plots for the October check in.

Reads data/processed/hourly.csv and saves figures to figures/:
  1. heatmap.png - carbon intensity, date x hour of day
  2. elbow.png - k-means inertia and silhouette score vs. k
  3. day_types.png - cluster-center daily curves
  4. day_types_month.png - how often each day type occurs in each month
  5. clusters_pca.png - every day as a point in 2D (PCA), colored by cluster
  6. pca_components.png - the hourly pattern each PCA axis represents
"""
from pathlib import Path
import matplotlib.pyplot as plt
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.metrics import silhouette_score

FIG = Path("figures")
K = 5 # TODO choose from elbow.png and justify in the README
# I'm doing 4 because 3 has the largest change so I'm doing largest change plus 1 as we learned in lecture
NORMALIZE = False # True = subtract each day's mean


def load_days() -> pd.DataFrame:
    df = pd.read_csv("data/processed/hourly.csv", parse_dates=["period_utc"], index_col="period_utc")
    ci = df["carbon_intensity"]
    days = ci.groupby([ci.index.date, ci.index.hour]).mean().unstack()
    days.index = pd.to_datetime(days.index)
    return days  # rows = days, columns = hour 0..23 (UTC)

def heatmap(days: pd.DataFrame) -> None:
    fig, ax = plt.subplots(figsize=(12, 4))
    im = ax.imshow(days.T, aspect="auto", origin="lower", cmap="viridis",
                   extent=[0, len(days), 0, 24])
    ticks = range(0, len(days), 90)
    ax.set_xticks(list(ticks), [days.index[i].strftime("%b %Y") for i in ticks], rotation=45)
    ax.set_ylabel("hour of day (UTC)")
    ax.set_title("ISO New England hourly carbon intensity")
    fig.colorbar(im, label="gCO2/kWh")
    fig.tight_layout()
    fig.savefig(FIG / "heatmap.png", dpi=150)

def elbow(X) -> None:
    ks = range(2, 11) # k range 2-11
    inertia, sil = [], [] # track shil score and enetria to compare
    # shil measures both cohesion and separation
    # inertia measures internal compactness 
    for k in ks:
        km = KMeans(n_clusters=k, n_init=10, random_state=0).fit(X) # run kmeans 
        inertia.append(km.inertia_)
        sil.append(silhouette_score(X, km.labels_))
    # plot the data collected and save it to an image
    fig, ax1 = plt.subplots(figsize=(6, 4))
    ax1.plot(ks, inertia, "o-", label="inertia")
    ax1.set_xlabel("k"); ax1.set_ylabel("inertia (within-cluster SSE)")
    ax2 = ax1.twinx()
    ax2.plot(ks, sil, "s--", color="tab:orange", label="silhouette")
    ax2.set_ylabel("silhouette score")
    fig.legend(loc="upper right")
    ax1.set_title("Choosing k")
    fig.tight_layout()
    fig.savefig(FIG / "elbow.png", dpi=150)

def day_types(days: pd.DataFrame, X) -> None:
    km = KMeans(n_clusters=K, n_init=10, random_state=0).fit(X) # fit k means
    # runs 10 times from different starting points and keeps the run with the lowest inertia
    labels = pd.Series(km.labels_, index=days.index) # attach labels to dates

    # plot carbon intensity clusters by hour of day
    #ran kmeans then plotted the  average  carbon-intensity for each group by the hour of the day to show the differences in the groups
    fig, ax = plt.subplots(figsize=(7, 4))
    for k in range(K):
        ax.plot(range(24), days[labels == k].mean(), label=f"type {k} (n={sum(labels == k)} days)")
    ax.set_xlabel("hour of day (UTC)"); ax.set_ylabel("gCO₂/kWh")
    ax.set_title(f"Daily carbon-intensity profiles (k-means, k={K})")
    ax.legend()
    fig.tight_layout()
    fig.savefig(FIG / "day_types.png", dpi=150)

    # plot each day type by month
    counts = pd.crosstab(labels.index.month, labels).rename_axis(index="month", columns="type")
    ax = counts.plot(kind="bar", stacked=True, figsize=(7, 4))
    ax.set_ylabel("number of days"); ax.set_title("Day types by month")
    plt.tight_layout()
    plt.savefig(FIG / "day_types_month.png", dpi=150)
    print(counts)
    return km


def cluster_scatter(X, km) -> None:
    """Project each 24-hour day onto its top 2 principal components and color by cluster.

    PCA here is SVD of the mean-centered day x hour matrix where each axis is one of the linear patterns days are built from.
    """
    pca = PCA(n_components=2).fit(X) # make the PCA with 2 componenets (internally runs SVD)
    pts = pca.transform(X) # project (shape (1090, 2)
    centers = pca.transform(km.cluster_centers_) # map centers
    var = pca.explained_variance_ratio_

    # plot the actual clusetring with knn
    fig, ax = plt.subplots(figsize=(7, 5))
    for k in range(K):
        m = km.labels_ == k # mask for the days in each cluster
        ax.scatter(pts[m, 0], pts[m, 1], s=8, alpha=0.5, label=f"type {k}") # plot only those days, in one color
    # plotting
    ax.scatter(centers[:, 0], centers[:, 1], c="black", marker="X", s=150, label="centers")
    ax.set_xlabel(f"PC1 ({var[0]:.0%} of variance)")
    ax.set_ylabel(f"PC2 ({var[1]:.0%} of variance)")
    ax.set_title(f"Days in PCA space, colored by k-means cluster (k={K})")
    ax.legend()
    fig.tight_layout()
    fig.savefig(FIG / "clusters_pca.png", dpi=150)

    # each axis is the hourly pattern each component represents
    # loading is the weight a principal component puts on each original variable
    # plotting
    fig, ax = plt.subplots(figsize=(7, 3))
    for i in range(2):
        ax.plot(range(24), pca.components_[i], label=f"PC{i + 1}")
    ax.axhline(0, color="gray", lw=0.5)
    ax.set_xlabel("hour of day (UTC)"); ax.set_ylabel("loading")
    ax.set_title("What each PCA axis represents")
    ax.legend()
    fig.tight_layout()
    fig.savefig(FIG / "pca_components.png", dpi=150)

    # PC1: all positive and about equal, so every hour counts the same. A day above average at every hour gets a high score.
    # PC2: negative at night, positive during the day. A day that is above average during the day and below average at night gets a high score. If both are above average, the two parts should partly cancel.


def main() -> None:
    FIG.mkdir(exist_ok=True)
    days = load_days()
    heatmap(days)
    complete = days.dropna()
    print(f"{len(complete)} complete days of {len(days)} (dropped days with missing hours)")
    X = complete.sub(complete.mean(axis=1), axis=0) if NORMALIZE else complete
    elbow(X)
    km = day_types(complete, X)
    cluster_scatter(X, km)
    print(f"figures saved to {FIG}/")


if __name__ == "__main__":
    main()