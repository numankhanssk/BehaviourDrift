import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest

from src.memory import LocalMemory, get_memory_backend


def test_local_memory_store_and_get_roundtrip(tmp_path):
    mem = LocalMemory(path=tmp_path / "mem.json")
    mem.store_fingerprint("octocat/demo", "2026-W20", [40, 1, 6, 40.0], {"status": "flagged"})

    history = mem.get_history("octocat/demo")
    assert len(history) == 1
    assert history[0]["week"] == "2026-W20"
    assert history[0]["vector"] == [40, 1, 6, 40.0]
    assert history[0]["detection_result"] == {"status": "flagged"}


def test_local_memory_upsert_replaces_same_week(tmp_path):
    mem = LocalMemory(path=tmp_path / "mem.json")
    mem.store_fingerprint("octocat/demo", "2026-W20", [1, 1, 0, 1.0], {"status": "normal"})
    mem.store_fingerprint("octocat/demo", "2026-W20", [40, 1, 6, 40.0], {"status": "flagged"})

    history = mem.get_history("octocat/demo")
    assert len(history) == 1, "storing the same entity+week twice should overwrite, not append"
    assert history[0]["detection_result"] == {"status": "flagged"}


def test_local_memory_keeps_weeks_sorted(tmp_path):
    mem = LocalMemory(path=tmp_path / "mem.json")
    mem.store_fingerprint("octocat/demo", "2026-W22", [1, 1, 0, 1.0], {})
    mem.store_fingerprint("octocat/demo", "2026-W20", [1, 1, 0, 1.0], {})
    mem.store_fingerprint("octocat/demo", "2026-W21", [1, 1, 0, 1.0], {})

    weeks = [r["week"] for r in mem.get_history("octocat/demo")]
    assert weeks == ["2026-W20", "2026-W21", "2026-W22"]


def test_local_memory_unknown_entity_returns_empty_list(tmp_path):
    mem = LocalMemory(path=tmp_path / "mem.json")
    assert mem.get_history("nobody/nothing") == []


def test_get_memory_backend_defaults_to_local_without_qdrant_url(monkeypatch):
    monkeypatch.delenv("QDRANT_URL", raising=False)
    backend = get_memory_backend()
    assert isinstance(backend, LocalMemory)


def test_get_memory_backend_falls_back_to_local_when_qdrant_unreachable(monkeypatch):
    # QDRANT_URL set but pointing nowhere valid, and/or qdrant_client not installed —
    # either way get_memory_backend() must not raise, it must fall back.
    monkeypatch.setenv("QDRANT_URL", "http://localhost:1/not-a-real-qdrant")
    backend = get_memory_backend()
    assert isinstance(backend, LocalMemory)
