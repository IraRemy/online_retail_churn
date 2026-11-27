"""Step 3 - Build the time-split snapshots (Week 4 design).

For a cutoff date T:
  * Features use ONLY purchases in the 90 days before T:  [T-90, T)
  * Eligible customers ("regular, recent buyers"):
      - at least 3 distinct purchase dates in [T-90, T)
      - at least 1 purchase in the last 30 days [T-30, T)
  * Target: 1 if NO purchase in the next 60 days [T, T+60), else 0.

Cutoffs: train = 1 Apr / 1 May / 1 Jun 2011, validation = 1 Aug 2011,
final test = 1 Oct 2011 (locked until the model is chosen).

Features per customer:
  RFM     : recency_days, log_frequency, log_monetary
  Timing  : usual_gap (median gap between purchase dates),
            gap_spread (std of gaps), delay_ratio (recency / usual_gap)
"""
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
CLEAN = ROOT / "data" / "processed" / "retail_clean.csv"
OUT = ROOT / "data" / "processed"

TRAIN_CUTOFFS = ["2011-04-01", "2011-05-01", "2011-06-01"]
VAL_CUTOFF = "2011-08-01"
TEST_CUTOFF = "2011-10-01"

RFM_FEATURES = ["recency_days", "log_frequency", "log_monetary"]
TIMING_FEATURES = ["usual_gap", "gap_spread", "delay_ratio"]


def load_clean() -> pd.DataFrame:
    df = pd.read_csv(CLEAN, dtype={"InvoiceNo": str, "StockCode": str},
                     parse_dates=["InvoiceDate"])
    df["date"] = df["InvoiceDate"].dt.normalize()
    return df


def build_snapshot(df: pd.DataFrame, cutoff: str) -> pd.DataFrame:
    T = pd.Timestamp(cutoff)
    hist = df[(df["date"] >= T - pd.Timedelta(days=90)) & (df["date"] < T)]
    future = df[(df["date"] >= T) & (df["date"] < T + pd.Timedelta(days=60))]

    g = hist.groupby("CustomerID")
    feat = pd.DataFrame({
        "last_date": g["date"].max(),
        "n_dates": g["date"].nunique(),
        "monetary": g["Revenue"].sum(),
    })

    recent = hist[hist["date"] >= T - pd.Timedelta(days=30)]
    feat["recent_30d"] = feat.index.isin(recent["CustomerID"].unique())

    # Eligibility: regular (>=3 purchase dates in 90d) and recent (buy in last 30d)
    feat = feat[(feat["n_dates"] >= 3) & feat["recent_30d"]].copy()

    feat["recency_days"] = (T - feat["last_date"]).dt.days
    feat["log_frequency"] = np.log1p(feat["n_dates"])
    feat["log_monetary"] = np.log1p(feat["monetary"])

    # Timing features from gaps between distinct purchase dates in the window
    gaps = (hist[hist["CustomerID"].isin(feat.index)]
            .drop_duplicates(["CustomerID", "date"])
            .sort_values(["CustomerID", "date"])
            .assign(gap=lambda x: x.groupby("CustomerID")["date"].diff().dt.days)
            .dropna(subset=["gap"])
            .groupby("CustomerID")["gap"])
    feat["usual_gap"] = gaps.median()
    feat["gap_spread"] = gaps.std().fillna(0.0)
    feat["delay_ratio"] = feat["recency_days"] / feat["usual_gap"].clip(lower=1)

    # Target: no purchase in the next 60 days
    buyers = set(future["CustomerID"].unique())
    feat["target_no_purchase"] = (~feat.index.isin(buyers)).astype(int)

    feat["cutoff"] = cutoff
    cols = (["cutoff"] + RFM_FEATURES + TIMING_FEATURES
            + ["n_dates", "monetary", "target_no_purchase"])
    return feat[cols].reset_index()


def build_all(verbose: bool = True) -> dict:
    df = load_clean()
    out = {}
    train_parts = [build_snapshot(df, c) for c in TRAIN_CUTOFFS]
    out["train"] = pd.concat(train_parts, ignore_index=True)
    out["validation"] = build_snapshot(df, VAL_CUTOFF)
    out["test"] = build_snapshot(df, TEST_CUTOFF)

    if verbose:
        for c, part in zip(TRAIN_CUTOFFS, train_parts):
            print(f"  train cutoff {c}: {len(part):>4} customers, "
                  f"{part['target_no_purchase'].mean():.1%} no-purchase")
        for name in ["train", "validation", "test"]:
            s = out[name]
            print(f"{name:>10}: {len(s):>4} customers, "
                  f"base rate {s['target_no_purchase'].mean():.1%} "
                  f"({s['target_no_purchase'].sum()} non-buyers)")
    return out


if __name__ == "__main__":
    snaps = build_all()
    for name, snap in snaps.items():
        path = OUT / f"snapshot_{name}.csv"
        snap.to_csv(path, index=False)
        print(f"Saved {path}")
