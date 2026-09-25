import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.report import render_html


def _base_report(**overrides):
    week = {
        "week": "2026-W20",
        "status": "flagged",
        "anomaly_score": -0.31,
        "explanation": "Normal explanation text.",
        "explanation_backend": "template",
        "commit_messages": ["fix bug"],
    }
    week.update(overrides)
    return {
        "entity_id": "octocat/demo",
        "summary": {"total_weeks": 1, "flagged_weeks": 1, "insufficient_history_weeks": 0},
        "weeks": [week],
    }


def test_render_html_escapes_malicious_commit_message():
    report = _base_report(commit_messages=["<script>alert('pwned')</script>"])
    html_out = render_html(report)

    assert "<script>alert" not in html_out
    assert "&lt;script&gt;" in html_out


def test_render_html_escapes_malicious_entity_id():
    report = _base_report()
    report["entity_id"] = "<img src=x onerror=alert(1)>/demo"
    html_out = render_html(report)

    assert "<img src=x onerror" not in html_out
    assert "&lt;img" in html_out


def test_render_html_escapes_malicious_llm_explanation():
    report = _base_report(explanation="Looks fine <script>document.location='https://evil.example'</script>")
    html_out = render_html(report)

    assert "<script>document.location" not in html_out
    assert "&lt;script&gt;" in html_out


def test_render_html_normal_content_still_renders_readable():
    report = _base_report()
    html_out = render_html(report)

    assert "octocat/demo" in html_out
    assert "Normal explanation text." in html_out
    assert "fix bug" in html_out
