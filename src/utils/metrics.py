# src/utils/metrics.py

import numpy as np


def pct_change(previous, current):
    """
    Computes simple percentage change.
    Example:
        pct_change(100, 120) = 0.20 (20% increase)
    """
    if previous == 0:
        return 0
    return (current - previous) / previous


def safe_mean(values):
    """
    Returns float mean of list or array.
    """
    if len(values) == 0:
        return 0.0
    return float(np.mean(values))


def z_test_proportions(p1, n1, p2, n2):
    """
    Two-proportion Z test for CTR comparison.
    Returns: (z_score, p_value)

    p1 = CTR in period 1
    n1 = impressions in period 1
    p2 = CTR in period 2
    n2 = impressions in period 2
    """
    from math import sqrt
    from scipy.stats import norm

    # pooled probability
    pooled_p = (p1 * n1 + p2 * n2) / (n1 + n2)

    # standard error
    se = sqrt(pooled_p * (1 - pooled_p) * (1/n1 + 1/n2))
    if se == 0:
        return 0, 1.0  # no significance possible

    z = (p1 - p2) / se
    p_value = 2 * (1 - norm.cdf(abs(z)))

    return float(z), float(p_value)
