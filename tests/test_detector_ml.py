import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.vectorizer import build_weekly_matrix
from src.detector_ml import detect_drift_ml


def test_stable_activity_not_flagged_ml():
    stable = {
        f"2026-W{i:02d}": {"commit_count": 10, "authors": {"a", "b", "c"}, "dependency_touches": 0}
        for i in range(10, 16)
    }
    weeks, matrix = build_weekly_matrix(stable)
    results = detect_drift_ml(weeks, matrix)
    flagged = [r for r in results if r["status"] == "flagged"]
    assert flagged == [], f"Expected no flags on perfectly stable activity, got: {flagged}"


def test_clear_anomaly_is_flagged_ml():
    data = {
        "2026-W10": {"commit_count": 10, "authors": {"a", "b", "c"}, "dependency_touches": 0},
        "2026-W11": {"commit_count": 11, "authors": {"a", "b", "c"}, "dependency_touches": 0},
        "2026-W12": {"commit_count": 9,  "authors": {"a", "b"},      "dependency_touches": 1},
        "2026-W13": {"commit_count": 12, "authors": {"a", "b", "c"}, "dependency_touches": 0},
        "2026-W14": {"commit_count": 40, "authors": {"a"},           "dependency_touches": 6},
    }
    weeks, matrix = build_weekly_matrix(data)
    results = detect_drift_ml(weeks, matrix)
    last = results[-1]
    assert last["status"] == "flagged"
    assert last["anomaly_score"] is not None


def test_ml_reduces_false_positive_vs_zscore():
    """
    This is the specific case that motivated the swap: a mild, non-anomalous bump
    (week 19-equivalent) that the pure z-score detector flagged, but that a
    reasonable observer wouldn't call real drift. The ML model should NOT flag it.
    """
    data = {
        "2026-W16": {"commit_count": 10, "authors": {"a", "b", "c"}, "dependency_touches": 0},
        "2026-W17": {"commit_count": 11, "authors": {"a", "b", "c"}, "dependency_touches": 0},
        "2026-W18": {"commit_count": 9,  "authors": {"a", "b"},      "dependency_touches": 1},
        "2026-W19": {"commit_count": 12, "authors": {"a", "b", "c"}, "dependency_touches": 0},
    }
    weeks, matrix = build_weekly_matrix(data)
    results = detect_drift_ml(weeks, matrix)
    assert results[-1]["status"] == "normal", (
        f"Expected the mild bump to be classified normal by the ML model, got: {results[-1]}"
    )


if __name__ == "__main__":
    test_stable_activity_not_flagged_ml()
    test_clear_anomaly_is_flagged_ml()
    test_ml_reduces_false_positive_vs_zscore()
    print("All ML detector tests passed.")
