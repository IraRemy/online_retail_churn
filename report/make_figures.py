"""Projector-ready EDA and results figures for the final deck.

Large fonts, berry palette, white background, no chart titles (the slide
title carries the message). Output: report/assets/*.png
"""
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT / "src"))

from explore import cohort_retention, load_clean  # noqa: E402
from models import FEATURE_SETS, fit_logistic  # noqa: E402

PROC = ROOT / "data" / "processed"
OUT = ROOT / "outputs"
ASSETS = HERE / "assets"

INK, MUTED, GRID = "#33202C", "#716572", "#EBE2E6"
RASP, AMBER, GRAY = "#C0507C", "#C98A2D", "#8A8A93"

plt.rcParams.update({
    "font.family": "Calibri" if "Calibri" in {f.name for f in matplotlib.font_manager.fontManager.ttflist} else "DejaVu Sans",
    "font.size": 16,
    "axes.labelsize": 16, "xtick.labelsize": 15, "ytick.labelsize": 15,
    "axes.labelcolor": MUTED, "xtick.color": MUTED, "ytick.color": MUTED,
    "axes.edgecolor": GRID, "figure.facecolor": "white", "axes.facecolor": "white",
})
FIG = (8.0, 5.0)


def style(ax, grid_axis="y"):
    ax.spines[["top", "right"]].set_visible(False)
    ax.spines[["left", "bottom"]].set_color(GRID)
    getattr(ax, f"{grid_axis}axis").grid(True, color=GRID, linewidth=1)
    ax.set_axisbelow(True)
    ax.tick_params(length=0)


def save(fig, name):
    fig.tight_layout(pad=0.6)
    fig.savefig(ASSETS / name, dpi=200)
    plt.close(fig)
    print("saved", name)


def pct_axis(ax, axis="y"):
    fmt = lambda v, _: f"{v:.0%}"
    getattr(ax, f"{axis}axis").set_major_formatter(fmt)


def rate_bars(ax, labels, rates, colors, fmt="{:.0%}", pad=0.006):
    bars = ax.bar(labels, rates, color=colors, width=0.62, zorder=2)
    for b, v in zip(bars, rates):
        ax.text(b.get_x() + b.get_width() / 2, v + pad, fmt.format(v),
                ha="center", va="bottom", fontsize=18, fontweight="bold",
                color=INK, zorder=4,
                bbox=dict(facecolor="white", edgecolor="none", pad=1.5))
    return bars


def main():
    ASSETS.mkdir(exist_ok=True)
    clean = load_clean()
    clean["month"] = clean["InvoiceDate"].dt.to_period("M")
    snaps = pd.concat([pd.read_csv(PROC / "snapshot_train.csv"),
                       pd.read_csv(PROC / "snapshot_validation.csv")],
                      ignore_index=True)

    # 1. Monthly active customers (seasonality) ---------------------------
    active = clean.groupby("month")["CustomerID"].nunique().loc["2010-12":"2011-11"]
    fig, ax = plt.subplots(figsize=FIG)
    labels = [p.strftime("%b") for p in active.index]
    colors = [RASP if p.month in (9, 10, 11) else GRAY for p in active.index]
    bars = ax.bar(range(len(active)), active.values, color=colors, width=0.7, zorder=2)
    for b, v, p in zip(bars, active.values, active.index):
        if p.month in (9, 10, 11) or p.month == 1:
            ax.text(b.get_x() + b.get_width() / 2, v + 20, f"{v:,}", ha="center",
                    va="bottom", fontsize=15, fontweight="bold", color=INK)
    ax.set_xticks(range(len(active)), labels)
    ax.set_ylabel("Customers who bought that month")
    ax.set_ylim(0, active.max() * 1.12)
    style(ax)
    save(fig, "fig_seasonality.png")

    # 2. Revenue concentration (Pareto) -----------------------------------
    rev = clean.groupby("CustomerID")["Revenue"].sum().sort_values(ascending=False)
    cum = rev.cumsum().values / rev.sum()
    x = np.arange(1, len(rev) + 1) / len(rev) * 100
    top10 = cum[int(np.ceil(0.1 * len(rev))) - 1]
    top20 = cum[int(np.ceil(0.2 * len(rev))) - 1]
    fig, ax = plt.subplots(figsize=FIG)
    ax.fill_between(x, cum * 100, color=RASP, alpha=0.12, zorder=1)
    ax.plot(x, cum * 100, color=RASP, lw=3.5, zorder=2)
    ax.plot([0, 100], [0, 100], color=GRAY, lw=1.8, ls="--", zorder=1)
    ax.text(74, 64, "if every customer\nspent the same", color=GRAY, fontsize=14,
            ha="left", va="top")
    for xx, yy in [(10, top10), (20, top20)]:
        ax.scatter([xx], [yy * 100], color=INK, s=60, zorder=3)
    ax.annotate(f"Top 10% of customers\n= {top10:.0%} of revenue",
                xy=(10, top10 * 100), xytext=(36, 30), va="top",
                fontsize=17, fontweight="bold", color=INK,
                arrowprops=dict(arrowstyle="-", color=MUTED, lw=1.2))
    ax.annotate(f"Top 20% = {top20:.0%}", xy=(20, top20 * 100),
                xytext=(30, top20 * 100 - 4), fontsize=15, color=INK,
                arrowprops=dict(arrowstyle="-", color=MUTED, lw=1.2))
    ax.set_xlabel("% of customers, biggest spenders first")
    ax.set_ylabel("% of yearly revenue")
    ax.set_xlim(0, 100); ax.set_ylim(0, 102)
    style(ax)
    save(fig, "fig_revenue_concentration.png")

    # 3. New vs returning revenue -----------------------------------------
    first = clean.groupby("CustomerID")["month"].min().rename("cohort")
    df = clean.join(first, on="CustomerID")
    df["kind"] = np.where(df["month"] == df["cohort"], "new", "returning")
    piv = (df.groupby(["month", "kind"])["Revenue"].sum().unstack(fill_value=0)
             .loc["2011-01":"2011-11"] / 1000)
    fig, ax = plt.subplots(figsize=FIG)
    xs = range(len(piv))
    ax.bar(xs, piv["returning"], color=RASP, width=0.7, zorder=2,
           label="Returning customers")
    ax.bar(xs, piv["new"], bottom=piv["returning"], color=GRAY, width=0.7,
           zorder=2, label="New customers", edgecolor="white", linewidth=1.5)
    ax.set_xticks(xs, [p.strftime("%b") for p in piv.index])
    ax.set_ylabel("Revenue (thousand GBP)")
    ax.legend(frameon=False, fontsize=15, loc="upper left", labelcolor=INK)
    style(ax)
    save(fig, "fig_new_vs_returning.png")

    # 4. Cohort retention heatmap -----------------------------------------
    ret = cohort_retention(clean.drop(columns=["month"]))
    data = ret.values[:, :7]
    data_rows = ret.index
    fig, ax = plt.subplots(figsize=FIG)
    ax.imshow(data, cmap="RdPu", vmin=0, vmax=60, aspect="auto")
    n_c = data.shape[0]
    for i in range(n_c):
        for j in range(min(7, ret.shape[1] - i)):
            v = data[i, j]
            ax.text(j, i, f"{v:.0f}%", ha="center", va="center", fontsize=14.5,
                    color="white" if v > 40 else INK, fontweight="bold" if j == 0 else None)
    ax.set_xticks(range(7), ["Start", "+1", "+2", "+3", "+4", "+5", "+6"])
    ax.set_yticks(range(n_c), [p.strftime("%b %y") for p in data_rows], fontsize=14)
    ax.set_xlabel("Months after first purchase")
    ax.set_ylabel("Month of first purchase")
    for s in ax.spines.values():
        s.set_visible(False)
    ax.tick_params(length=0)
    save(fig, "fig_cohort.png")

    # 5. Risk by purchase dates (habit depth) -----------------------------
    snaps["freq_b"] = pd.cut(snaps["n_dates"], [2, 3, 5, 8, 99],
                             labels=["3", "4-5", "6-8", "9+"])
    r = snaps.groupby("freq_b", observed=True)["target_no_purchase"].mean()
    fig, ax = plt.subplots(figsize=FIG)
    rate_bars(ax, [f"{k} orders" for k in r.index], r.values,
              [RASP, RASP, GRAY, GRAY])
    base = snaps["target_no_purchase"].mean()
    ax.axhline(base, color=INK, ls=":", lw=1.5, zorder=1.5)
    ax.text(3.45, base + 0.004, f"average {base:.0%}", ha="right", va="bottom",
            fontsize=14, color=INK)
    ax.set_xlabel("Separate order days in the last 90 days")
    ax.set_ylabel("Stopped buying in next 60 days")
    ax.set_ylim(0, 0.25)
    pct_axis(ax)
    style(ax)
    save(fig, "fig_risk_habit.png")

    # 6. Risk by days since last order (silence) ---------------------------
    snaps["rec_b"] = pd.cut(snaps["recency_days"], [-1, 7, 14, 21, 30],
                            labels=["0-7", "8-14", "15-21", "22-30"])
    r = snaps.groupby("rec_b", observed=True)["target_no_purchase"].mean()
    fig, ax = plt.subplots(figsize=FIG)
    rate_bars(ax, [f"{k} days" for k in r.index], r.values,
              [GRAY, GRAY, GRAY, RASP])
    ax.axhline(base, color=INK, ls=":", lw=1.5, zorder=1.5)
    ax.text(-0.45, base + 0.004, f"average {base:.0%}", ha="left", va="bottom",
            fontsize=14, color=INK)
    ax.set_xlabel("Days since the customer's last order")
    ax.set_ylabel("Stopped buying in next 60 days")
    ax.set_ylim(0, 0.25)
    pct_axis(ax)
    style(ax)
    save(fig, "fig_risk_silence.png")

    # 7. What the model looks at (standardized coefficients) --------------
    train = pd.read_csv(PROC / "snapshot_train.csv")
    feats = FEATURE_SETS["rfm_timing"]
    model = fit_logistic(train, feats)
    coefs = pd.Series(model[-1].coef_[0], index=feats)
    names = {
        "recency_days": "Days since last order",
        "log_frequency": "Number of order days",
        "log_monetary": "Money spent (90 days)",
        "usual_gap": "Usual gap between orders",
        "gap_spread": "How irregular the gaps are",
        "delay_ratio": "Lateness vs own rhythm",
    }
    coefs = coefs.rename(names).sort_values()
    fig, ax = plt.subplots(figsize=FIG)
    cols = [RASP if v > 0 else GRAY for v in coefs.values]
    ax.barh(coefs.index, coefs.values, color=cols, height=0.62, zorder=2)
    for i, v in enumerate(coefs.values):
        ax.text(v + (0.03 if v >= 0 else -0.03), i, f"{v:+.2f}",
                ha="left" if v >= 0 else "right", va="center", fontsize=15,
                fontweight="bold", color=INK)
    ax.axvline(0, color=INK, lw=1.2)
    lim = max(abs(coefs.values)) * 1.45
    ax.set_xlim(-lim, lim)
    ax.set_xlabel("Effect on risk score  (left = safer, right = riskier)")
    style(ax, "x")
    ax.tick_params(axis="y", labelsize=15, labelcolor=INK)
    save(fig, "fig_model_drivers.png")
    coefs.to_csv(ASSETS / "model_drivers.csv", header=["coef"])

    # 8. Gains: share of leavers found vs share of customers contacted -----
    t = pd.read_csv(OUT / "test_scores_all.csv").sort_values("risk_score",
                                                             ascending=False)
    y = t["target_no_purchase"].to_numpy()
    capture = np.concatenate([[0], np.cumsum(y) / y.sum()])
    share = np.arange(len(y) + 1) / len(y)
    fig, ax = plt.subplots(figsize=FIG)
    ax.plot(share * 100, capture * 100, color=RASP, lw=3.5, zorder=2,
            label="Using the risk score")
    ax.plot([0, 100], [0, 100], color=GRAY, lw=2, ls="--", zorder=1,
            label="Contacting at random")
    for p in (0.10, 0.30):
        k = int(np.ceil(p * len(y)))
        c = capture[k]
        ax.scatter([p * 100], [c * 100], color=INK, s=60, zorder=3)
        ax.annotate(f"Top {p:.0%} contacted\n= {c:.0%} of leavers found",
                    xy=(p * 100, c * 100),
                    xytext=(14, 13) if p < 0.2 else (40, 37), va="top",
                    fontsize=15, fontweight="bold", color=INK,
                    arrowprops=dict(arrowstyle="-", color=MUTED, lw=1.2))
    ax.set_xlabel("% of eligible customers contacted (riskiest first)")
    ax.set_ylabel("% of real leavers found")
    ax.set_xlim(0, 100); ax.set_ylim(0, 102)
    ax.legend(frameon=False, fontsize=15, loc="lower right", labelcolor=INK)
    style(ax)
    save(fig, "fig_gains.png")

    # 9. Validation bake-off + final test ----------------------------------
    import json
    S = json.loads((OUT / "eda_summary.json").read_text())
    v, ft = S["validation"], S["final_test"]
    fig, ax = plt.subplots(figsize=FIG)
    labels = ["Random\npick", "Recency\nonly", "RFM\nmodel", "RFM +\ntiming"]
    vals = [v["base_rate"], v["recency"]["precision"], v["rfm"]["precision"],
            v["rfm_timing"]["precision"]]
    rate_bars(ax, labels, vals, [GRAY, RASP, RASP, AMBER], fmt="{:.0%}")
    ax.set_ylabel("Share of the top-10% list who\nreally stopped buying")
    ax.set_ylim(0, 0.38)
    pct_axis(ax)
    style(ax)
    save(fig, "fig_bakeoff.png")


if __name__ == "__main__":
    main()
