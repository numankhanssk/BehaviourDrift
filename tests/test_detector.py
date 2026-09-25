import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.vectorizer import build_weekly_matrix
from src.detector import detect_drift


def test_stable_activity_not_flagged():
    stable = {
        f"2026-W{i:02d}": {"commit_count": 10, "authors": {"a", "b", "c"}, "dependency_touches": 0}
        for i in range(10, 16)
    }
    weeks, matrix = build_weekly_matrix(stable)
    results = detect_drift(weeks, matrix)
    flagged = [r for r in results if r["status"] == "flagged"]
    assert flagged == [], f"Expected no flags on perfectly stable activity, got: {flagged}"


def test_clear_anomaly_is_flagged():
    data = {
        "2026-W10": {"commit_count": 10, "authors": {"a", "b", "c"}, "dependency_touches": 0},
        "2026-W11": {"commit_count": 11, "authors": {"a", "b", "c"}, "dependency_touches": 0},
        "2026-W12": {"commit_count": 9,  "authors": {"a", "b"},      "dependency_touches": 1},
        "2026-W13": {"commit_count": 12, "authors": {"a", "b", "c"}, "dependency_touches": 0},
        "2026-W14": {"commit_count": 40, "authors": {"a"},           "dependency_touches": 6},
    }
    weeks, matrix = build_weekly_matrix(data)
    results = detect_drift(weeks, matrix)
    last = results[-1]
    assert last["status"] == "flagged"
    assert any(f["feature"] == "commit_count" for f in last["flagged_features"])


def test_insufficient_history_not_falsely_flagged():
    data = {
        "2026-W10": {"commit_count": 10, "authors": {"a"}, "dependency_touches": 0},
        "2026-W11": {"commit_count": 999, "authors": {"a"}, "dependency_touches": 99},  # wild but too early
    }
    weeks, matrix = build_weekly_matrix(data)
    results = detect_drift(weeks, matrix)
    assert all(r["status"] == "insufficient_history" for r in results)


if __name__ == "__main__":
    test_stable_activity_not_flagged()
    test_clear_anomaly_is_flagged()
    test_insufficient_history_not_falsely_flagged()
    print("All tests passed.")
