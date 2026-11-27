"""Step 7 - Score every regular customer at the LATEST date in the data.

This is the operational list a business would use "this week": the frozen
model (chosen on validation, trained on the training snapshots only) is
applied at the day after the last invoice. Outcomes are unknown here; the
locked 1 Oct 2011 test is what proves the score works.

Outputs:
  outputs/latest_scores.csv   - every eligible regular, ranked, with plain-English reasons
  outputs/model_drivers.csv   - standardized model coefficients (what raises / lowers risk)
"""
from pathlib import Path

import numpy as np
import pandas as pd

from models import FEATURE_SETS, fit_logistic
from snapshots import build_snapshot, load_clean

ROOT = Path(__file__).resolve().parents[1]
PROC = ROOT / "data" / "processed"
OUT = ROOT / "outputs"

DRIVER_NAMES = {
    "recency_days": "Days since last order",
    "log_frequency": "Number of order days",
    "log_monetary": "Money spent (90 days)",
    "usual_gap": "Usual gap between orders",
    "gap_spread": "How irregular the gaps are",
    "delay_ratio": "Lateness vs own rhythm",
}


def reasons(row) -> str:
    out = []
    if row["n_dates"] <= 3:
        out.append("shallow habit")
    if row["delay_ratio"] >= 1:
        out.append(f"late ({row['recency_days']}d quiet, usually {row['usual_gap']:.0f}d)")
    elif row["recency_days"] >= 21:
        out.append(f"quiet {row['recency_days']} days")
    if row["gap_spread"] >= 15:
        out.append("irregular orders")
    if row["monetary"] < 300:
        out.append("low spend")
    return ", ".join(out) if out else "mild mix of signals"


def main():
    chosen = (OUT / "models" / "chosen_model.txt").read_text().strip()
    feats = FEATURE_SETS[chosen]
    train = pd.read_csv(PROC / "snapshot_train.csv")
    model = fit_logistic(train, feats)

    clean = load_clean()
    cutoff = (clean["date"].max() + pd.Timedelta(days=1)).strftime("%Y-%m-%d")
    snap = build_snapshot(clean, cutoff).drop(columns=["target_no_purchase"])
    snap["risk_score"] = model.predict_proba(snap[feats])[:, 1]
    snap = snap.sort_values("risk_score", ascending=False).reset_index(drop=True)

    n = len(snap)
    rank_pct = (np.arange(n) + 1) / n
    snap["risk_level"] = np.select([rank_pct <= 0.10, rank_pct <= 0.30],
                                   ["High", "Medium"], "Low")
    snap["reasons"] = snap.apply(reasons, axis=1)
    snap["rank"] = np.arange(1, n + 1)

    cols = ["rank", "CustomerID", "risk_level", "risk_score", "recency_days",
            "n_dates", "monetary", "usual_gap", "gap_spread", "delay_ratio",
            "reasons", "cutoff"]
    snap[cols].to_csv(OUT / "latest_scores.csv", index=False)

    coefs = pd.DataFrame({"feature": feats,
                          "label": [DRIVER_NAMES[f] for f in feats],
                          "coef": model[-1].coef_[0]})
    coefs.to_csv(OUT / "model_drivers.csv", index=False)

    high = snap[snap["risk_level"] == "High"]
    print(f"Latest scoring date: {cutoff}  (model: {chosen})")
    print(f"  eligible regulars : {n}")
    print(f"  High risk (top 10%): {len(high)} customers, "
          f"GBP {high['monetary'].sum():,.0f} of 90-day spend")
    print(f"Saved {OUT / 'latest_scores.csv'} and {OUT / 'model_drivers.csv'}")


if __name__ == "__main__":
    main()
