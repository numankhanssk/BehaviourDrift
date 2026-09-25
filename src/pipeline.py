"""
pipeline.py — End-to-end orchestration: collect -> vectorize -> detect (Isolation Forest,
primary) -> (if flagged) gather commit evidence -> investigate (LLM reasons over evidence)
-> store -> report. This is the thing  demo actually runs.
"""

from src.collector import collect_weekly_activity, fetch_commit_messages_for_week
from src.vectorizer import build_weekly_matrix, FEATURE_NAMES
from src.detector_ml import detect_drift_ml
from src.memory import get_memory_backend
from src.agent import investigate


def _run(entity_id: str, weeks: list, matrix, memory, raw_weekly_activity: dict = None,
         owner: str = None, repo: str = None, fetch_evidence: bool = False):
    detection_results = detect_drift_ml(weeks, matrix)

    report = {"entity_id": entity_id, "weeks": []}
    for i, res in enumerate(detection_results):
        week_report = dict(res)
        memory.store_fingerprint(entity_id, res["week"], matrix[i].tolist(), res)

        if res["flagged"]:
            commit_messages = None
            if fetch_evidence and raw_weekly_activity is not None and owner and repo:
                shas = raw_weekly_activity.get(res["week"], {}).get("shas", [])
                if shas:
                    commit_messages = fetch_commit_messages_for_week(owner, repo, shas)

            investigation = investigate(
                entity_id, res["week"], res["flagged_features"],
                anomaly_score=res["anomaly_score"], commit_messages=commit_messages,
            )
            week_report["explanation"] = investigation["explanation"]
            week_report["explanation_backend"] = investigation["backend"]
            week_report["commit_messages"] = commit_messages

        report["weeks"].append(week_report)

    report["summary"] = {
        "total_weeks": len(weeks),
        "flagged_weeks": sum(1 for r in detection_results if r["flagged"]),
        "insufficient_history_weeks": sum(1 for r in detection_results if r["status"] == "insufficient_history"),
    }
    return report


def run_pipeline(owner: str, repo: str, max_pages: int = 2, inspect_files: bool = True):
    entity_id = f"{owner}/{repo}"
    memory = get_memory_backend()

    raw = collect_weekly_activity(owner, repo, max_pages=max_pages, inspect_files=inspect_files)
    if not raw:
        return {"entity_id": entity_id, "error": "No activity found (empty or inaccessible repo)."}

    weeks, matrix = build_weekly_matrix(raw)
    return _run(entity_id, weeks, matrix, memory, raw_weekly_activity=raw,
                owner=owner, repo=repo, fetch_evidence=True)


def run_pipeline_from_synthetic(entity_id: str, weekly_activity: dict):
   
    memory = get_memory_backend()
    weeks, matrix = build_weekly_matrix(weekly_activity)
    return _run(entity_id, weeks, matrix, memory, fetch_evidence=False)


if __name__ == "__main__":
    # Offline demo — no GitHub API calls, so it works even when rate-limited.
    sample = {
        "2026-W16": {"commit_count": 10, "authors": {"a", "b", "c"}, "dependency_touches": 0},
        "2026-W17": {"commit_count": 11, "authors": {"a", "b", "c"}, "dependency_touches": 0},
        "2026-W18": {"commit_count": 9,  "authors": {"a", "b"},      "dependency_touches": 1},
        "2026-W19": {"commit_count": 12, "authors": {"a", "b", "c"}, "dependency_touches": 0},
        "2026-W20": {"commit_count": 40, "authors": {"a"},           "dependency_touches": 6},
    }
    import json
    result = run_pipeline_from_synthetic("demo/synthetic-repo", sample)
    print(json.dumps(result, indent=2))
