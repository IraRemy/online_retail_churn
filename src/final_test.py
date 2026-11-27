"""Step 5 - Run the chosen, frozen model ONCE on the locked 1 Oct 2011 test.

This answers the project question: which regular customers may stop buying
in the next 60 days?  Output: the top 10% follow-up list for the retailer
(outputs/followup_list.csv) and the honest test metrics next to the base rate.

Run this only after evaluate_validation.py has chosen a model.
"""
from pathlib import Path

import numpy as np
import pandas as pd

from models import FEATURE_SETS, evaluate, fit_logistic, recency_scores, top_k

ROOT = Path(__file__).resolve().parents[1]
PROC = ROOT / "data" / "processed"
OUT = ROOT / "outputs"
MODELS = OUT / "models"


def main():
    chosen = (MODELS / "chosen_model.txt").read_text().strip()
    train = pd.read_csv(PROC / "snapshot_train.csv")
    test = pd.read_csv(PROC / "snapshot_test.csv")
    y = test["target_no_purchase"].to_numpy()

    if chosen == "recency":
        scores = recency_scores(test)
    else:
        feats = FEATURE_SETS[chosen]
        model = fit_logistic(train, feats)
        scores = model.predict_proba(test[feats])[:, 1]

    r = evaluate(y, scores)
    print(f"FINAL TEST - 1 Oct 2011 (used once), model: {chosen}")
    print(f"  customers        : {r['n']}")
    print(f"  base rate        : {r['base_rate']:.1%} ({int(y.sum())} non-buyers)")
    print(f"  top 10% list     : {r['k']} customers")
    print(f"  correct on list  : {r['hits']}  ({r['precision_at_k']:.1%})")
    print(f"  lift vs random   : {r['lift']:.1f}x")
    print(f"  average precision: {r['average_precision']:.3f}")

    test = test.copy()
    test["risk_score"] = scores
    test["on_followup_list"] = False
    k = top_k(len(test))
    top_idx = np.argsort(-scores)[:k]
    test.iloc[top_idx, test.columns.get_loc("on_followup_list")] = True

    cols = ["CustomerID", "risk_score", "recency_days", "n_dates", "monetary",
            "usual_gap", "delay_ratio", "on_followup_list"]
    followup = (test.loc[test["on_followup_list"], cols]
                .sort_values("risk_score", ascending=False))
    followup.to_csv(OUT / "followup_list.csv", index=False)
    test[cols + ["target_no_purchase"]].sort_values(
        "risk_score", ascending=False).to_csv(OUT / "test_scores_all.csv",
                                              index=False)
    print(f"\nFollow-up list ({k} customers) saved to {OUT / 'followup_list.csv'}")
    print(f"All test scores saved to {OUT / 'test_scores_all.csv'}")


if __name__ == "__main__":
    main()
