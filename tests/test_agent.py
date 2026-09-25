import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
import requests

from src import agent

SAMPLE_FLAGS = [
    {"feature": "commit_count", "z_score": 26.39, "current": 40.0, "baseline_mean": 10.5},
]


def test_investigate_uses_template_when_no_api_keys(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)

    result = agent.investigate("octocat/demo", "2026-W20", SAMPLE_FLAGS, anomaly_score=-0.2)

    assert result["backend"] == "template"
    assert "octocat/demo" in result["explanation"]
    assert "2026-W20" in result["explanation"]


def test_investigate_uses_claude_when_call_succeeds(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "fake-key")
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)

    class FakeResponse:
        def raise_for_status(self):
            pass

        def json(self):
            return {"content": [{"type": "text", "text": "Claude's explanation."}]}

    monkeypatch.setattr(agent.requests, "post", lambda *a, **k: FakeResponse())

    result = agent.investigate("octocat/demo", "2026-W20", SAMPLE_FLAGS)

    assert result["backend"] == "claude"
    assert result["explanation"] == "Claude's explanation."


def test_investigate_falls_back_to_gemini_when_claude_fails(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "fake-key")
    monkeypatch.setenv("GEMINI_API_KEY", "fake-key")

    def fake_post(url, *a, **k):
        if "anthropic.com" in url:
            raise requests.exceptions.RequestException("Claude is down")
        return type("R", (), {
            "raise_for_status": lambda self: None,
            "json": lambda self: {"candidates": [{"content": {"parts": [{"text": "Gemini's explanation."}]}}]},
        })()

    monkeypatch.setattr(agent.requests, "post", fake_post)

    result = agent.investigate("octocat/demo", "2026-W20", SAMPLE_FLAGS)

    assert result["backend"] == "gemini"
    assert result["explanation"] == "Gemini's explanation."


def test_investigate_falls_back_to_template_when_all_backends_fail(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "fake-key")
    monkeypatch.setenv("GEMINI_API_KEY", "fake-key")

    def fake_post(*a, **k):
        raise requests.exceptions.RequestException("network down")

    monkeypatch.setattr(agent.requests, "post", fake_post)

    result = agent.investigate("octocat/demo", "2026-W20", SAMPLE_FLAGS)

    assert result["backend"] == "template"
    assert "octocat/demo" in result["explanation"]
