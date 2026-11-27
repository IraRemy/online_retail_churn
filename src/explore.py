"""Step 2 - Week 3 exploration: monthly activity and cohort retention.

Produces:
  outputs/figures/monthly_active_customers.png
  outputs/figures/cohort_retention.png
and prints the numbers behind the Week 3 slides.
"""
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
CLEAN = ROOT / "data" / "processed" / "retail_clean.csv"
FIGS = ROOT / "outputs" / "figures"

INK = "#1F2937"
MUTED = "#6B7280"
BAR = "#2A7E8C"       # single teal hue - one series, magnitude
GRID = "#E5E7EB"


def load_clean() -> pd.DataFrame:
    return pd.read_csv(CLEAN, dtype={"InvoiceNo": str, "StockCode": str},
                       parse_dates=["InvoiceDate"])


def style_axis(ax):
    ax.spines[["top", "right"]].set_visible(False)
    ax.spines[["left", "bottom"]].set_color(GRID)
    ax.tick_params(colors=MUTED, labelsize=9)
    ax.yaxis.grid(True, color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)


def monthly_active(df: pd.DataFrame) -> pd.Series:
    df = df.copy()
    df["month"] = df["InvoiceDate"].dt.to_period("M")
    active = df.groupby("month")["CustomerID"].nunique()
    # Dec 2010 .. Nov 2011; Dec 2011 excluded (data stops on 9 December)
    return active.loc["2010-12":"2011-11"]


def plot_monthly(active: pd.Series) -> None:
    labels = [p.strftime("%b %y") for p in active.index]
    fig, ax = plt.subplots(figsize=(9, 4.5))
    bars = ax.bar(labels, active.values, color=BAR, width=0.65, zorder=2)
    for b, v in zip(bars, active.values):
        ax.text(b.get_x() + b.get_width() / 2, v + 18, f"{v:,}",
                ha="center", va="bottom", fontsize=8, color=INK)
    style_axis(ax)
    ax.set_title("Active customers per month (Dec 2010 - Nov 2011)",
                 color=INK, fontsize=12, loc="left")
    ax.set_ylabel("Customers with >=1 purchase", color=MUTED, fontsize=9)
    fig.tight_layout()
    fig.savefig(FIGS / "monthly_active_customers.png", dpi=150)
    plt.close(fig)


def cohort_retention(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["month"] = df["InvoiceDate"].dt.to_period("M")
    first = df.groupby("CustomerID")["month"].min().rename("cohort")
    df = df.join(first, on="CustomerID")
    df["offset"] = (df["month"] - df["cohort"]).apply(lambda d: d.n)
    counts = (df.groupby(["cohort", "offset"])["CustomerID"].nunique()
                .unstack(fill_value=0))
    sizes = counts[0]
    retention = counts.divide(sizes, axis=0) * 100
    return retention.loc["2010-12":"2011-11"]


def plot_cohorts(ret: pd.DataFrame) -> None:
    fig, ax = plt.subplots(figsize=(9, 5))
    data = ret.values
    im = ax.imshow(data, cmap="Blues", vmin=0, vmax=50, aspect="auto")
    ax.set_yticks(range(len(ret.index)),
                  [p.strftime("%b %y") for p in ret.index], fontsize=8, color=MUTED)
    ax.set_xticks(range(data.shape[1]), range(data.shape[1]), fontsize=8, color=MUTED)
    ax.set_xlabel("Months since first purchase", color=MUTED, fontsize=9)
    n_cohorts, n_offsets = data.shape
    for i in range(n_cohorts):
        max_offset = n_offsets - 1 - i  # later cohorts are observed fewer months
        for j in range(min(n_offsets, max_offset + 1)):
            val = data[i, j]
            color = "white" if val > 30 else INK
            ax.text(j, i, f"{val:.0f}", ha="center", va="center",
                    fontsize=7, color=color)
    ax.set_title("Cohort retention: % of cohort active N months later",
                 color=INK, fontsize=12, loc="left")
    cbar = fig.colorbar(im, ax=ax, shrink=0.8)
    cbar.ax.tick_params(labelsize=8, colors=MUTED)
    cbar.set_label("% active", color=MUTED, fontsize=9)
    fig.tight_layout()
    fig.savefig(FIGS / "cohort_retention.png", dpi=150)
    plt.close(fig)


if __name__ == "__main__":
    FIGS.mkdir(parents=True, exist_ok=True)
    df = load_clean()

    active = monthly_active(df)
    print("Active customers per month:")
    for p, v in active.items():
        print(f"  {p.strftime('%b %Y')}: {v:,}")
    plot_monthly(active)

    ret = cohort_retention(df)
    later = ret.iloc[:, 1:]
    vals = later.values[later.values > 0]
    print(f"\nCohort retention after month 0: typical range "
          f"{np.percentile(vals, 25):.0f}-{np.percentile(vals, 75):.0f}% per month")
    plot_cohorts(ret)
    print(f"\nFigures saved in {FIGS}")
