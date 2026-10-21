"""How a career becomes a score, and where the Hall of Fame line sits."""

import numpy as np
import pandas as pd

# How much each career statistic is worth. Changing a weight is a methodology
# change: say why in the PR, and the report comment shows what it moved.
WEIGHTS = {
    "slams": 1.0,
    "slam_finals": 0.3,
    "masters": 0.3,
    "tour_finals": 0.5,
    "titles": 0.05,
    "weeks_no1": 0.01,
    "weeks_top10": 0.002,
    "win_pct": 2.0,
}

# Players who left the tour this many years ago become eligible (ITHF rule).
ELIGIBLE_AFTER = 5


def score(features: pd.DataFrame) -> pd.Series:
    return sum((features[k] * w for k, w in WEIGHTS.items()), start=pd.Series(0.0, features.index))


def ithf_rule(features: pd.DataFrame) -> pd.Series:
    """Baseline zero: the Hall's own automatic-ballot rule for singles players.

    Five major titles, or three majors plus at least 13 weeks at No. 1.
    Any model we publish has to beat this.
    """
    return (features["slams"] >= 5) | ((features["slams"] >= 3) & (features["weeks_no1"] >= 13))


def fit_threshold(scores: pd.Series, inducted: pd.Series) -> float:
    """The score cut-off that maximises F1 on the training years."""
    best, best_f1 = float("inf"), -1.0
    for t in np.unique(scores):
        pred = scores >= t
        tp = (pred & inducted).sum()
        f1 = 2 * tp / (pred.sum() + inducted.sum()) if tp else 0.0
        if f1 > best_f1:
            best, best_f1 = float(t), f1
    return best
