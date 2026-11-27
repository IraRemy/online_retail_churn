"""Model definitions and evaluation metrics (Week 4 + Week 5).

Models
  recency     : rank by days since last purchase (bigger = riskier), random ties
  rfm         : logistic regression on recency, log frequency, log spending
  rfm_timing  : same model plus usual_gap, gap_spread, delay_ratio (Week 5)

Metric: precision in the top 10% shortlist (k = ceil(0.10 * n)),
lift over the base rate, and Average Precision. Bootstrap CI on AP difference.
"""
import math

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from snapshots import RFM_FEATURES, TIMING_FEATURES

SEED = 42

FEATURE_SETS = {
    "rfm": RFM_FEATURES,
    "rfm_timing": RFM_FEATURES + TIMING_FEATURES,
}


def recency_scores(snap: pd.DataFrame, seed: int = SEED) -> np.ndarray:
    """Risk score = recency in days; random jitter breaks ties."""
    rng = np.random.default_rng(seed)
    return snap["recency_days"].to_numpy(float) + rng.uniform(0, 0.5, len(snap))


def fit_logistic(train: pd.DataFrame, features: list[str]):
    model = make_pipeline(StandardScaler(),
                          LogisticRegression(max_iter=1000, random_state=SEED))
    model.fit(train[features], train["target_no_purchase"])
    return model


def top_k(n: int, share: float = 0.10) -> int:
    return math.ceil(n * share)


def evaluate(y: np.ndarray, scores: np.ndarray, share: float = 0.10) -> dict:
    n = len(y)
    k = top_k(n, share)
    order = np.argsort(-scores)
    hits = int(y[order[:k]].sum())
    base = y.mean()
    precision = hits / k
    return {
        "n": n, "k": k, "hits": hits,
        "precision_at_k": precision,
        "base_rate": base,
        "lift": precision / base,
        "average_precision": average_precision_score(y, scores),
    }


def bootstrap_ap_diff(y, scores_a, scores_b, n_boot=2000, seed=SEED):
    """95% CI for AP(a) - AP(b) by bootstrap over customers."""
    rng = np.random.default_rng(seed)
    n = len(y)
    diffs = []
    for _ in range(n_boot):
        idx = rng.integers(0, n, n)
        if y[idx].sum() == 0:
            continue
        diffs.append(average_precision_score(y[idx], scores_a[idx])
                     - average_precision_score(y[idx], scores_b[idx]))
    return np.percentile(diffs, [2.5, 97.5])
