"""
collector.py — Pulls raw activity from GitHub for a single repo and buckets it into
calendar weeks. Set GITHUB_TOKEN env var to raise the limit to 5000/hr.
"""

import os
import time
import requests
from datetime import datetime, timezone
from collections import defaultdict

GITHUB_API = "https://api.github.com"
DEPENDENCY_FILES = {
    "package.json", "package-lock.json", "requirements.txt", "pyproject.toml",
    "poetry.lock", "go.mod", "go.sum", "Gemfile", "Gemfile.lock", "pom.xml",
    "build.gradle", "Cargo.toml", "Cargo.lock",
}


def _headers():
    
    token = os.environ.get("GITHUB_TOKEN")
    
    h = {"Accept": "application/vnd.github+json"}
    if token:
        h["Authorization"] = f"Bearer {token}"
    return h


def _week_key(iso_date: str) -> str:
    """Bucket an ISO timestamp into a 'YYYY-WW' calendar week key."""
    dt = datetime.strptime(iso_date, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    year, week, _ = dt.isocalendar()
    return f"{year}-W{week:02d}"


def fetch_commits(owner: str, repo: str, max_pages: int = 3, per_page: int = 100):
    """Fetch recent commits with author + date. Paginates up to max_pages."""
    commits = []
    for page in range(1, max_pages + 1):
        url = f"{GITHUB_API}/repos/{owner}/{repo}/commits"
        resp = requests.get(
            url, headers=_headers(),
            params={"per_page": per_page, "page": page}, timeout=15
        )
        if resp.status_code == 404:
            raise RuntimeError(
                f"Repository '{owner}/{repo}' not found (404). Check the owner/repo spelling, "
                f"or set GITHUB_TOKEN if it's a private repo you have access to."
            )
        if resp.status_code == 403:
            raise RuntimeError(
                f"GitHub API rate-limited (403). Set GITHUB_TOKEN env var. "
                f"Response: {resp.text[:200]}"
            )
        resp.raise_for_status()
        batch = resp.json()
        if not batch:
            break
        commits.extend(batch)
        if len(batch) < per_page:
            break
        time.sleep(0.2)  # be polite to unauthenticated rate limit
    return commits


def fetch_commit_files(owner: str, repo: str, sha: str):
    """Fetch the list of files changed in a single commit (used to detect dependency-file churn)."""
    url = f"{GITHUB_API}/repos/{owner}/{repo}/commits/{sha}"
    resp = requests.get(url, headers=_headers(), timeout=15)
    if resp.status_code != 200:
        return []
    return [f["filename"] for f in resp.json().get("files", [])]


def fetch_commit_messages_for_week(owner: str, repo: str, shas: list, limit: int = 15):
    """
    Fetches commit messages for a specific list of SHAs (typically: the SHAs belonging
    to one flagged week). This is the raw evidence handed to the LLM agent so it can
    reason about content, not just aggregate counts - e.g. spotting messages like
    "temp bypass auth check" or "update ci token" that a pure number can't see.
    Deliberately called only for flagged weeks, not every week, to keep API calls bounded.
    """
    messages = []
    for sha in shas[:limit]:
        url = f"{GITHUB_API}/repos/{owner}/{repo}/commits/{sha}"
        resp = requests.get(url, headers=_headers(), timeout=15)
        if resp.status_code == 200:
            msg = resp.json().get("commit", {}).get("message", "").split("\n")[0]
            messages.append(msg)
        time.sleep(0.1)
    return messages


def collect_weekly_activity(owner: str, repo: str, max_pages: int = 3, inspect_files: bool = True):
    """
    Returns: dict[week_key] -> {
        'commit_count': int,
        'authors': set(str),
        'dependency_touches': int,
        'shas': [str]
    }
    """
    commits = fetch_commits(owner, repo, max_pages=max_pages)
    weeks = defaultdict(lambda: {
        "commit_count": 0, "authors": set(), "dependency_touches": 0, "shas": []
    })

    for c in commits:
        commit_date = c["commit"]["author"]["date"]
        wk = _week_key(commit_date)
        author = (c.get("author") or {}).get("login") or c["commit"]["author"]["email"]
        weeks[wk]["commit_count"] += 1
        weeks[wk]["authors"].add(author)
        weeks[wk]["shas"].append(c["sha"])

    if inspect_files:
        # Only inspect files for the most recent N commits to keep API calls bounded
        recent_shas = [c["sha"] for c in commits[:30]]
        sha_to_week = {}
        for c in commits:
            if c["sha"] in recent_shas:
                sha_to_week[c["sha"]] = _week_key(c["commit"]["author"]["date"])

        for sha in recent_shas:
            files = fetch_commit_files(owner, repo, sha)
            if any(f.split("/")[-1] in DEPENDENCY_FILES for f in files):
                wk = sha_to_week[sha]
                weeks[wk]["dependency_touches"] += 1
            time.sleep(0.1)

    return dict(weeks)


if __name__ == "__main__":
    import sys
    import json
    owner, repo = (sys.argv[1:3] if len(sys.argv) > 2 else ("pallets", "flask"))
    data = collect_weekly_activity(owner, repo, max_pages=1, inspect_files=True)
    printable = {
        wk: {**v, "authors": sorted(v["authors"])} for wk, v in data.items()
    }
    print(json.dumps(printable, indent=2))
