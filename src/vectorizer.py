"""
vectorizer.py — Converts raw weekly activity dicts (from collector.py) into fixed-length
numeric feature vectors. This is the "behavioral identity" representation everything
else operates on.
"""

import numpy as np

FEATURE_NAMES = [
    "commit_count",
    "unique_authors",
    "dependency_touches",
    "commits_per_author",   # concentration: low = many people, high = few people doing a lot
]


def week_to_vector(week_data: dict) -> np.ndarray:
    commit_count = week_data.get("commit_count", 0)
    # "authors" may be a list (e.g. from JSON-loaded memory) or a set (from the collector);
    # len() works on both, so no need to special-case the type.
    unique_authors = len(week_data.get("authors", []))
    dependency_touches = week_data.get("dependency_touches", 0)
    commits_per_author = commit_count / unique_authors if unique_authors else 0.0

    return np.array([commit_count, unique_authors, dependency_touches, commits_per_author], dtype=float)


def build_weekly_matrix(weekly_activity: dict):
    """
    weekly_activity: dict[week_key] -> raw activity dict
    Returns: (sorted_week_keys: list[str], matrix: np.ndarray of shape [n_weeks, n_features])
    """
    weeks = sorted(weekly_activity.keys())
    matrix = np.array([week_to_vector(weekly_activity[wk]) for wk in weeks])
    return weeks, matrix


if __name__ == "__main__":
    sample = {
        "2026-W20": {"commit_count": 12, "authors": {"a", "b", "c"}, "dependency_touches": 0},
        "2026-W21": {"commit_count": 9, "authors": {"a", "b"}, "dependency_touches": 1},
        "2026-W22": {"commit_count": 40, "authors": {"a"}, "dependency_touches": 6},  # anomalous week
    }
    weeks, matrix = build_weekly_matrix(sample)
    for wk, row in zip(weeks, matrix):
        print(wk, dict(zip(FEATURE_NAMES, row)))
