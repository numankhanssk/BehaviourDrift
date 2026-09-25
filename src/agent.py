import os
import json
import requests


def _template_explanation(entity_id: str, week: str, flagged_features: list,
                            anomaly_score: float = None, commit_messages: list = None) -> str:
    if not flagged_features and anomaly_score is None:
        return f"No significant drift detected for {entity_id} in {week}."
    lines = [f"Behavioral drift flagged for {entity_id} in {week}:"]
    if anomaly_score is not None:
        lines.append(f"- Isolation Forest anomaly score: {anomaly_score} (more negative = more anomalous)")
    for f in flagged_features:
        direction = "spiked" if f["z_score"] > 0 else "dropped"
        lines.append(
            f"- {f['feature'].replace('_', ' ')} {direction} to {f['current']} "
            f"(baseline avg {f['baseline_mean']}, z-score {f['z_score']})"
        )
    if commit_messages:
        lines.append(f"- Sample commit messages this week: {commit_messages[:5]}")
    lines.append(
        "This combination deviates from this entity's own historical baseline; "
        "it does not match a known vulnerability signature, which is precisely the "
        "gap signature-based tools (Dependabot, Snyk) don't cover."
    )
    return "\n".join(lines)


def _claude_explanation(entity_id: str, week: str, flagged_features: list,
                          anomaly_score: float = None, commit_messages: list = None) -> str:
    api_key_present = bool(os.environ.get("ANTHROPIC_API_KEY"))
    if not api_key_present:
        raise RuntimeError("ANTHROPIC_API_KEY not set")

    evidence_parts = [f"Statistical feature deviations from baseline:\n{json.dumps(flagged_features, indent=2)}"]
    if anomaly_score is not None:
        evidence_parts.append(
            f"\nIsolation Forest anomaly score for this week: {anomaly_score} "
            f"(the model flagged this week as anomalous relative to this entity's own history; "
            f"more negative = more anomalous)."
        )
    if commit_messages:
        evidence_parts.append(
            f"\nActual commit messages from this week (raw evidence, reason about content "
            f"not just the numbers above):\n" + "\n".join(f"- {m}" for m in commit_messages)
        )

    prompt = (
        f"You are a security analyst assistant. An automated system (an Isolation Forest "
        f"anomaly detection model, not a rule threshold) flagged behavioral drift for "
        f"repository '{entity_id}' in week {week}.\n\n"
        + "\n".join(evidence_parts) +
        f"\n\nWrite a 3-4 sentence, plain-English risk explanation for a DevSecOps engineer. "
        f"Reason over BOTH the statistical deviation AND the actual commit message content if "
        f"provided — e.g. do any messages sound like they're bypassing checks, adding "
        f"credentials, or disabling security features, versus looking like a legitimate "
        f"release/refactor? Do not overstate certainty — this is a statistical flag, not a "
        f"confirmed incident."
    )
    resp = requests.post(
        "https://api.anthropic.com/v1/messages",
        headers={
            "x-api-key": os.environ["ANTHROPIC_API_KEY"],
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        },
        json={
            "model": "claude-sonnet-4-6",
            "max_tokens": 300,
            "messages": [{"role": "user", "content": prompt}],
        },
        timeout=30,
    )
    resp.raise_for_status()
    data = resp.json()
    return "".join(block.get("text", "") for block in data.get("content", []) if block.get("type") == "text")


def _gemini_explanation(entity_id: str, week: str, flagged_features: list) -> str:
  
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY not set")

    prompt = (
        f"Behavioral drift flagged for repo '{entity_id}' in week {week}. "
        f"Deviations from baseline: {json.dumps(flagged_features)}. "
        f"Write a 3-4 sentence plain-English risk explanation for a DevSecOps engineer."
    )
    url = (
        "https://generativelanguage.googleapis.com/v1beta/models/"
        f"gemini-3.1-flash-lite:generateContent?key={api_key}"
    )
    resp = requests.post(
        url, json={"contents": [{"parts": [{"text": prompt}]}]}, timeout=30
    )
    resp.raise_for_status()
    data = resp.json()
    return data["candidates"][0]["content"]["parts"][0]["text"]


def investigate(entity_id: str, week: str, flagged_features: list,
                 anomaly_score: float = None, commit_messages: list = None) -> dict:
    """Returns {'explanation': str, 'backend': str} — always succeeds via fallback chain."""
    if os.environ.get("ANTHROPIC_API_KEY"):
        try:
            return {"explanation": _claude_explanation(entity_id, week, flagged_features,
                                                          anomaly_score, commit_messages),
                    "backend": "claude"}
        except Exception as e:
            print(f"[agent] Claude call failed ({e}); falling back.")
    if os.environ.get("GEMINI_API_KEY"):
        try:
            return {"explanation": _gemini_explanation(entity_id, week, flagged_features), "backend": "gemini"}
        except Exception as e:
            print(f"[agent] Gemini call failed ({e}); falling back.")
    return {"explanation": _template_explanation(entity_id, week, flagged_features,
                                                    anomaly_score, commit_messages),
            "backend": "template"}


if __name__ == "__main__":
    sample_flags = [
        {"feature": "commit_count", "z_score": 26.39, "current": 40.0, "baseline_mean": 10.5},
        {"feature": "dependency_touches", "z_score": 13.28, "current": 6.0, "baseline_mean": 0.25},
    ]
    result = investigate("octocat/demo-repo", "2026-W20", sample_flags)
    print(f"[backend used: {result['backend']}]\n")
    print(result["explanation"])
