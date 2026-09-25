import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest

from src.pipeline import run_pipeline_from_synthetic
from src.memory import LocalMemory

SAMPLE = {
    "2026-W16": {"commit_count": 10, "authors": {"a", "b", "c"}, "dependency_touches": 0},
    "2026-W17": {"commit_count": 11, "authors": {"a", "b", "c"}, "dependency_touches": 0},
    "2026-W18": {"commit_count": 9,  "authors": {"a", "b"},      "dependency_touches": 1},
    "2026-W19": {"commit_count": 12, "authors": {"a", "b", "c"}, "dependency_touches": 0},
    "2026-W20": {"commit_count": 40, "authors": {"a"},           "dependency_touches": 6},
}


@pytest.fixture(autouse=True)
def isolated_memory(monkeypatch, tmp_path):
    """
    Every pipeline test runs against a scratch LocalMemory instance instead of the real
    one. Without this, run_pipeline_from_synthetic() writes through to the project's
    actual data/local_memory.json (LocalMemory's default path is bound at class-definition
    time, so monkeypatching src.memory.LOCAL_STORE_PATH after import does NOT redirect
    it — get_memory_backend() must be patched directly). autouse=True so this applies to
    every test in this file without each one needing to remember to opt in.
    """
    scratch_mem = LocalMemory(path=tmp_path / "local_memory.json")
    monkeypatch.setattr("src.pipeline.get_memory_backend", lambda: scratch_mem)
    return scratch_mem


def test_run_pipeline_from_synthetic_flags_the_anomalous_week(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)

    report = run_pipeline_from_synthetic("demo/synthetic-repo", SAMPLE)

    assert report["entity_id"] == "demo/synthetic-repo"
    assert report["summary"]["total_weeks"] == 5
    assert report["summary"]["flagged_weeks"] == 1

    flagged = [w for w in report["weeks"] if w["status"] == "flagged"]
    assert len(flagged) == 1
    assert flagged[0]["week"] == "2026-W20"
    # a flagged week should always carry an explanation, even with no LLM keys set
    assert "explanation" in flagged[0]
    assert flagged[0]["explanation_backend"] == "template"


def test_run_pipeline_from_synthetic_writes_one_fingerprint_per_week(monkeypatch, isolated_memory):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)

    report = run_pipeline_from_synthetic("demo/synthetic-repo", SAMPLE)

    history = isolated_memory.get_history("demo/synthetic-repo")
    assert len(history) == len(SAMPLE)
    assert {r["week"] for r in history} == set(SAMPLE.keys())
    assert len(report["weeks"]) == len(SAMPLE)


def test_run_pipeline_from_synthetic_no_flags_on_stable_history(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)

    stable = {
        f"2026-W{i:02d}": {"commit_count": 10, "authors": {"a", "b", "c"}, "dependency_touches": 0}
        for i in range(10, 16)
    }
    report = run_pipeline_from_synthetic("demo/stable-repo", stable)
    assert report["summary"]["flagged_weeks"] == 0
