"""Step 2b - Business-risk EDA: where the money is exposed and who is about to leave.

Figures (outputs/figures/):
  revenue_concentration.png    - Pareto: a small share of customers holds most revenue
  new_vs_returning_revenue.png - monthly revenue split: new vs returning customers
  risk_by_recency.png          - no-purchase rate rises with days since last buy
  risk_by_frequency.png        - no-purchase rate falls with purchase regularity
  risk_by_delay.png            - no-purchase rate vs delay ratio (late vs usual rhythm)

Also writes outputs/eda_summary.json with every number the report deck needs.
"""
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from models import FEATURE_SETS, evaluate, fit_logistic
from snapshots import TEST_CUTOFF

ROOT = Path(__file__).resolve().parents[1]
PROC = ROOT / "data" / "processed"
OUT = ROOT / "outputs"
FIGS = OUT / "figures"

INK, MUTED, GRID = "#1F2937", "#6B7280", "#E5E7EB"
BAR = "#2A7E8C"
BAR2 = "#9CA3AF"


def style(ax):
    ax.spines[["top", "right"]].set_visible(False)
    ax.spines[["left", "bottom"]].set_color(GRID)
    ax.tick_params(colors=MUTED, labelsize=9)
    ax.yaxis.grid(True, color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)


def rate_bar(df, bucket_col, order, title, xlabel, fname):
    g = df.groupby(bucket_col, observed=True)["target_no_purchase"]
    rates, counts = g.mean().reindex(order), g.size().reindex(order)
    ticks = [f"{o}" + "\n" + f"n={n}" for o, n in zip(order, counts.values)]
    fig, ax = plt.subplots(figsize=(7, 4))
    bars = ax.bar(ticks, rates.values, color=BAR, width=0.6, zorder=2)
    for b, v in zip(bars, rates.values):
        ax.text(b.get_x() + b.get_width() / 2, v + 0.004, f"{v:.0%}",
                ha="center", va="bottom", fontsize=9, color=INK)
    ax.set_ylim(0, max(rates.values) * 1.22)
    style(ax)
    ax.yaxis.set_major_formatter(lambda v, _: f"{v:.0%}")
    ax.set_title(title, color=INK, fontsize=11, loc="left")
    ax.set_xlabel(xlabel, color=MUTED, fontsize=9, labelpad=8)
    fig.tight_layout()
    fig.savefig(FIGS / fname, dpi=150)
    plt.close(fig)
    return {o: {"rate": round(float(rates[o]), 4), "n": int(counts[o])}
            for o in order}


def main():
    FIGS.mkdir(parents=True, exist_ok=True)
    clean = pd.read_csv(PROC / "retail_clean.csv",
                        dtype={"InvoiceNo": str, "StockCode": str},
                        parse_dates=["InvoiceDate"])
    clean["month"] = clean["InvoiceDate"].dt.to_period("M")
    summary = {}

    # ---- 1. Revenue concentration (Pareto) --------------------------------
    rev = clean.groupby("CustomerID")["Revenue"].sum().sort_values(ascending=False)
    cum = rev.cumsum() / rev.sum()
    pct_customers = np.arange(1, len(rev) + 1) / len(rev)
    top10 = float(cum.iloc[int(np.ceil(0.10 * len(rev))) - 1])
    top20 = float(cum.iloc[int(np.ceil(0.20 * len(rev))) - 1])
    summary["revenue_concentration"] = {
        "customers": int(len(rev)),
        "total_revenue": round(float(rev.sum()), 2),
        "top10pct_share": round(top10, 4),
        "top20pct_share": round(top20, 4),
        "curve": [{"pct_customers": round(float(p), 3),
                   "pct_revenue": round(float(c), 3)}
                  for p, c in zip(pct_customers[::40], cum.values[::40])],
    }
    fig, ax = plt.subplots(figsize=(7, 4.2))
    ax.plot(pct_customers * 100, cum.values * 100, color=BAR, lw=2, zorder=2)
    ax.plot([0, 100], [0, 100], color=BAR2, lw=1.2, ls="--", zorder=1)
    ax.annotate(f"top 10% of customers\n= {top10:.0%} of revenue",
                xy=(10, top10 * 100), xytext=(22, top10 * 100 - 6),
                fontsize=9, color=INK,
                arrowprops=dict(arrowstyle="-", color=MUTED, lw=0.8))
    ax.scatter([10], [top10 * 100], color=INK, s=18, zorder=3)
    style(ax)
    ax.set_title("Revenue is concentrated in few customers", color=INK,
                 fontsize=11, loc="left")
    ax.set_xlabel("% of customers (best first)", color=MUTED, fontsize=9)
    ax.set_ylabel("% of total revenue", color=MUTED, fontsize=9)
    fig.tight_layout()
    fig.savefig(FIGS / "revenue_concentration.png", dpi=150)
    plt.close(fig)

    # ---- 2. New vs returning revenue per month ----------------------------
    first_month = clean.groupby("CustomerID")["month"].min().rename("cohort")
    df = clean.join(first_month, on="CustomerID")
    df["kind"] = np.where(df["month"] == df["cohort"], "new", "returning")
    piv = (df.groupby(["month", "kind"], observed=True)["Revenue"].sum()
             .unstack(fill_value=0).loc["2010-12":"2011-11"] / 1000)
    ret_share = float(piv["returning"].sum() / piv.sum().sum())
    summary["new_vs_returning"] = {
        "returning_share_of_revenue": round(ret_share, 4),
        "months": [{"month": p.strftime("%b %y"),
                    "new_k": round(float(r["new"]), 1),
                    "returning_k": round(float(r["returning"]), 1)}
                   for p, r in piv.iterrows()],
    }
    labels = [p.strftime("%b %y") for p in piv.index]
    fig, ax = plt.subplots(figsize=(9, 4.5))
    ax.bar(labels, piv["returning"], color=BAR, width=0.65, zorder=2,
           label="Returning customers")
    ax.bar(labels, piv["new"], bottom=piv["returning"], color=BAR2,
           width=0.65, zorder=2, label="New customers")
    style(ax)
    ax.set_ylabel("Revenue (thousand GBP)", color=MUTED, fontsize=9)
    ax.set_title("The business runs on returning customers "
                 f"({ret_share:.0%} of revenue)", color=INK, fontsize=11,
                 loc="left")
    ax.legend(frameon=False, fontsize=9, labelcolor=INK)
    fig.tight_layout()
    fig.savefig(FIGS / "new_vs_returning_revenue.png", dpi=150)
    plt.close(fig)

    # ---- 3-5. Who stops buying: risk by feature (train+validation) --------
    snaps = pd.concat([pd.read_csv(PROC / "snapshot_train.csv"),
                       pd.read_csv(PROC / "snapshot_validation.csv")],
                      ignore_index=True)
    summary["risk_pool"] = {
        "n": int(len(snaps)),
        "base_rate": round(float(snaps["target_no_purchase"].mean()), 4)}

    snaps["recency_b"] = pd.cut(snaps["recency_days"], [-1, 7, 14, 21, 30],
                                labels=["0-7 d", "8-14 d", "15-21 d", "22-30 d"])
    summary["risk_by_recency"] = rate_bar(
        snaps, "recency_b", ["0-7 d", "8-14 d", "15-21 d", "22-30 d"],
        "Risk of stopping rises with days since the last purchase",
        "Days since last purchase at the cutoff", "risk_by_recency.png")

    snaps["freq_b"] = pd.cut(snaps["n_dates"], [2, 3, 5, 8, 99],
                             labels=["3", "4-5", "6-8", "9+"])
    summary["risk_by_frequency"] = rate_bar(
        snaps, "freq_b", ["3", "4-5", "6-8", "9+"],
        "Regulars with few purchase dates are the fragile ones",
        "Distinct purchase dates in the last 90 days", "risk_by_frequency.png")

    snaps["delay_b"] = pd.cut(snaps["delay_ratio"], [-1, 0.5, 1, 2, 99],
                              labels=["<0.5x", "0.5-1x", "1-2x", ">2x"])
    summary["risk_by_delay"] = rate_bar(
        snaps, "delay_b", ["<0.5x", "0.5-1x", "1-2x", ">2x"],
        "Being late vs your usual rhythm is NOT a signal on its own",
        "Current wait vs usual gap between purchases (delay ratio)",
        "risk_by_delay.png")

    # ---- 6. Money on the line at the final cutoff -------------------------
    test = pd.read_csv(PROC / "snapshot_test.csv")
    followup = pd.read_csv(OUT / "followup_list.csv")
    flagged = test[test["CustomerID"].isin(followup["CustomerID"])]
    summary["money_at_risk"] = {
        "cutoff": TEST_CUTOFF,
        "list_size": int(len(flagged)),
        "list_90d_spend": round(float(flagged["monetary"].sum()), 2),
        "eligible_90d_spend": round(float(test["monetary"].sum()), 2),
        "avg_90d_spend_per_listed": round(float(flagged["monetary"].mean()), 2),
    }

    # ---- 7. Model scoreboard (validation + final test) --------------------
    val_res = pd.read_csv(OUT / "models" / "validation_results.csv", index_col=0)
    summary["validation"] = {
        m: {"hits": int(r["hits"]), "k": int(r["k"]),
            "precision": round(float(r["precision_at_k"]), 4),
            "lift": round(float(r["lift"]), 2),
            "ap": round(float(r["average_precision"]), 3)}
        for m, r in val_res.iterrows()}
    summary["validation"]["base_rate"] = round(float(val_res["base_rate"].iloc[0]), 4)

    chosen = (OUT / "models" / "chosen_model.txt").read_text().strip()
    train = pd.read_csv(PROC / "snapshot_train.csv")
    feats = FEATURE_SETS[chosen]
    model = fit_logistic(train, feats)
    scores = model.predict_proba(test[feats])[:, 1]
    r = evaluate(test["target_no_purchase"].to_numpy(), scores)
    summary["final_test"] = {
        "model": chosen, "n": r["n"], "k": r["k"], "hits": r["hits"],
        "precision": round(r["precision_at_k"], 4),
        "base_rate": round(r["base_rate"], 4),
        "lift": round(r["lift"], 2),
        "ap": round(r["average_precision"], 3)}

    # ---- monthly actives + one-time buyers (for the deck) -----------------
    active = clean.groupby("month")["CustomerID"].nunique().loc["2010-12":"2011-11"]
    summary["monthly_active"] = [{"month": p.strftime("%b %y"), "n": int(v)}
                                 for p, v in active.items()]
    one_time = float((clean.groupby("CustomerID")["InvoiceDate"]
                      .apply(lambda s: s.dt.normalize().nunique()) == 1).mean())
    summary["one_time_buyer_share"] = round(one_time, 4)

    (OUT / "eda_summary.json").write_text(json.dumps(summary, indent=2))
    print(json.dumps({k: v for k, v in summary.items()
                      if k not in ("new_vs_returning", "monthly_active",
                                   "revenue_concentration")}, indent=2))
    print(f"\ntop10pct_share={top10:.1%}  top20pct_share={top20:.1%}  "
          f"returning_share={ret_share:.1%}")
    print(f"Figures in {FIGS}\nSummary in {OUT / 'eda_summary.json'}")


if __name__ == "__main__":
    main()
