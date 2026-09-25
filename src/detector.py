"""
detector.py — Flags drift by comparing each week's vector against a rolling baseline
built from prior weeks. Deliberately statistical, not a trained ML model :
- Explainable by construction (every flag traces to specific z-scored features)
- No training data / cold-start problem
- Cheap: this is the "run on every entity, every week" tier from the cost-to-serve design.
  The LLM agent (agent.py) is only invoked for weeks this flags.
"""

import numpy as np
from src.vectorizer import FEATURE_NAMES

DEFAULT_Z_THRESHOLD = 2.0   # ~95th percentile for a normal distribution
MIN_BASELINE_WEEKS = 3      # need at least this many prior weeks to trust a baseline


def compute_baseline(matrix: np.ndarray):
    """mean/std per feature across all rows given."""
    mean = matrix.mean(axis=0)
    std = matrix.std(axis=0)
    std[std == 0] = 1e-6  # avoid divide-by-zero for flat features
    return mean, std


def detect_drift(weeks: list, matrix: np.ndarray, z_threshold: float = DEFAULT_Z_THRESHOLD):
    """
    Rolling baseline: for week i, baseline = weeks[0:i] (everything before it).
    Returns list of dicts, one per week (weeks before MIN_BASELINE_WEEKS are marked
    'insufficient_history' rather than silently skipped or falsely flagged).
    """
    results = []
    for i, wk in enumerate(weeks):
        if i < MIN_BASELINE_WEEKS:
            results.append({
                "week": wk,
                "status": "insufficient_history",
                "flagged": False,
                "z_scores": None,
            })
            continue

        history = matrix[:i]
        mean, std = compute_baseline(history)
        current = matrix[i]
        z_scores = (current - mean) / std

        flagged_features = [
            {"feature": FEATURE_NAMES[j], "z_score": round(float(z_scores[j]), 2),
             "current": float(current[j]), "baseline_mean": round(float(mean[j]), 2)}
            for j in range(len(z_scores)) if abs(z_scores[j]) >= z_threshold
        ]

        results.append({
            "week": wk,
            "status": "flagged" if flagged_features else "normal",
            "flagged": bool(flagged_features),
            "z_scores": {FEATURE_NAMES[j]: round(float(z_scores[j]), 2) for j in range(len(z_scores))},
            "flagged_features": flagged_features,
        })
    return results


if __name__ == "__main__":
    from src.vectorizer import build_weekly_matrix

    sample = {
        "2026-W16": {"commit_count": 10, "authors": {"a", "b", "c"}, "dependency_touches": 0},
        "2026-W17": {"commit_count": 11, "authors": {"a", "b", "c"}, "dependency_touches": 0},
        "2026-W18": {"commit_count": 9,  "authors": {"a", "b"},      "dependency_touches": 1},
        "2026-W19": {"commit_count": 12, "authors": {"a", "b", "c"}, "dependency_touches": 0},
        "2026-W20": {"commit_count": 40, "authors": {"a"},           "dependency_touches": 6},  # drift
    }
    weeks, matrix = build_weekly_matrix(sample)
    results = detect_drift(weeks, matrix)
    for r in results:
        print(r["week"], "->", r["status"], r.get("flagged_features") or "")
