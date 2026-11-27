"""Step 4 - Train on the 3 training snapshots, compare models on 1 Aug validation.

Week 4: recency ranking vs RFM logistic regression.
Week 5: add timing features; keep them only if they beat the baselines.
Writes the chosen model name to outputs/models/chosen_model.txt.
"""
from pathlib import Path

import pandas as pd

from models import (FEATURE_SETS, bootstrap_ap_diff, evaluate, fit_logistic,
                    recency_scores)

ROOT = Path(__file__).resolve().parents[1]
PROC = ROOT / "data" / "processed"
MODELS = ROOT / "outputs" / "models"


def plot_precision(results: dict, base_rate: float) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    INK, MUTED, GRID = "#1F2937", "#6B7280", "#E5E7EB"
    names = ["Random pick", "Recency ranking", "RFM model", "RFM + timing"]
    vals = [base_rate,
            results["recency"]["precision_at_k"],
            results["rfm"]["precision_at_k"],
            results["rfm_timing"]["precision_at_k"]]
    colors = ["#9CA3AF", "#2A7E8C", "#2A7E8C", "#2A7E8C"]
    fig, ax = plt.subplots(figsize=(7, 4))
    bars = ax.bar(names, vals, color=colors, width=0.6, zorder=2)
    for b, v in zip(bars, vals):
        ax.text(b.get_x() + b.get_width() / 2, v + 0.006, f"{v:.1%}",
                ha="center", va="bottom", fontsize=9, color=INK)
    ax.spines[["top", "right"]].set_visible(False)
    ax.spines[["left", "bottom"]].set_color(GRID)
    ax.tick_params(colors=MUTED, labelsize=9)
    ax.yaxis.grid(True, color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)
    ax.yaxis.set_major_formatter(lambda v, _: f"{v:.0%}")
    ax.set_title("Precision in the top 10% list (validation, 1 Aug 2011)",
                 color=INK, fontsize=11, loc="left")
    figdir = ROOT / "outputs" / "figures"
    figdir.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(figdir / "validation_precision.png", dpi=150)
    plt.close(fig)


def main():
    train = pd.read_csv(PROC / "snapshot_train.csv")
    val = pd.read_csv(PROC / "snapshot_validation.csv")
    y = val["target_no_purchase"].to_numpy()

    scores = {"recency": recency_scores(val)}
    for name, feats in FEATURE_SETS.items():
        model = fit_logistic(train, feats)
        scores[name] = model.predict_proba(val[feats])[:, 1]

    print(f"Validation: 1 Aug 2011, n={len(val)}, "
          f"base rate {y.mean():.1%} ({y.sum()} non-buyers)\n")
    results = {}
    for name, s in scores.items():
        r = evaluate(y, s)
        results[name] = r
        print(f"{name:>11}: top {r['k']} list -> {r['hits']} correct "
              f"({r['precision_at_k']:.1%}, lift {r['lift']:.1f}), "
              f"AP {r['average_precision']:.3f}")

    lo, hi = bootstrap_ap_diff(y, scores["rfm"], scores["recency"])
    print(f"\nBootstrap 95% CI, AP(rfm) - AP(recency): [{lo:+.2f}, {hi:+.2f}]"
          + ("  -> includes zero: no clear winner" if lo <= 0 <= hi else ""))
    lo2, hi2 = bootstrap_ap_diff(y, scores["rfm_timing"], scores["rfm"])
    print(f"Bootstrap 95% CI, AP(rfm_timing) - AP(rfm): [{lo2:+.2f}, {hi2:+.2f}]"
          + ("  -> includes zero" if lo2 <= 0 <= hi2 else ""))

    # Week 5 decision rule: timing features are kept only if they beat the
    # best baseline precision on validation; otherwise the simplest best
    # model by average precision wins.
    best_baseline_prec = max(results["recency"]["precision_at_k"],
                             results["rfm"]["precision_at_k"])
    if results["rfm_timing"]["precision_at_k"] > best_baseline_prec:
        chosen = "rfm_timing"
    else:
        chosen = max(["recency", "rfm"],
                     key=lambda m: results[m]["average_precision"])
    print(f"\nChosen model (frozen for the final test): {chosen}")

    plot_precision(results, y.mean())

    MODELS.mkdir(parents=True, exist_ok=True)
    (MODELS / "chosen_model.txt").write_text(chosen + "\n")
    pd.DataFrame(results).T.to_csv(MODELS / "validation_results.csv")
    print(f"Saved {MODELS / 'validation_results.csv'}")


if __name__ == "__main__":
    main()
