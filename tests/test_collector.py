import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest

from src.collector import collect_weekly_activity, fetch_commits


def _commit(sha, date, login=None, email="dev@example.com"):
    author = {"login": login} if login else None
    return {
        "sha": sha,
        "author": author,
        "commit": {"author": {"date": date, "email": email}},
    }


def test_fetch_commits_raises_clear_error_on_404(requests_mock):
    requests_mock.get(
        "https://api.github.com/repos/ghost-owner/ghost-repo/commits",
        status_code=404,
        json={"message": "Not Found"},
    )

    with pytest.raises(RuntimeError, match="not found"):
        fetch_commits("ghost-owner", "ghost-repo", max_pages=1)


def test_fetch_commits_raises_clear_error_on_403_rate_limit(requests_mock):
    requests_mock.get(
        "https://api.github.com/repos/some/repo/commits",
        status_code=403,
        text="API rate limit exceeded",
    )

    with pytest.raises(RuntimeError, match="rate-limited"):
        fetch_commits("some", "repo", max_pages=1)


def test_collect_weekly_activity_buckets_by_week_and_counts_authors(requests_mock):
    commits = [
        _commit("sha1", "2026-04-13T10:00:00Z", login="alice"),
        _commit("sha2", "2026-04-14T10:00:00Z", login="bob"),
        _commit("sha3", "2026-04-20T10:00:00Z", login="alice"),  # next ISO week
    ]
    requests_mock.get(
        "https://api.github.com/repos/octocat/demo/commits",
        json=commits,
    )
    # inspect_files=False so we don't need to mock per-commit file lookups here
    result = collect_weekly_activity("octocat", "demo", max_pages=1, inspect_files=False)

    weeks = sorted(result.keys())
    assert len(weeks) == 2
    first_week = result[weeks[0]]
    assert first_week["commit_count"] == 2
    assert first_week["authors"] == {"alice", "bob"}
    second_week = result[weeks[1]]
    assert second_week["commit_count"] == 1


def test_collect_weekly_activity_detects_dependency_touches(requests_mock):
    commits = [_commit("sha1", "2026-04-13T10:00:00Z", login="alice")]
    requests_mock.get(
        "https://api.github.com/repos/octocat/demo/commits",
        json=commits,
    )
    requests_mock.get(
        "https://api.github.com/repos/octocat/demo/commits/sha1",
        json={"files": [{"filename": "requirements.txt"}, {"filename": "src/app.py"}]},
    )

    result = collect_weekly_activity("octocat", "demo", max_pages=1, inspect_files=True)

    week = next(iter(result.values()))
    assert week["dependency_touches"] == 1


def test_collect_weekly_activity_empty_repo_returns_empty_dict(requests_mock):
    requests_mock.get(
        "https://api.github.com/repos/octocat/empty/commits",
        json=[],
    )
    result = collect_weekly_activity("octocat", "empty", max_pages=1, inspect_files=False)
    assert result == {}


def test_fetch_commits_stops_paginating_on_short_page(requests_mock):
    full_page = [_commit(f"sha{i}", "2026-04-13T10:00:00Z", login="alice") for i in range(100)]
    short_page = [_commit("sha-last", "2026-04-14T10:00:00Z", login="alice")]

    requests_mock.get(
        "https://api.github.com/repos/octocat/demo/commits",
        [{"json": full_page}, {"json": short_page}],
    )

    commits = fetch_commits("octocat", "demo", max_pages=5, per_page=100)
    # should stop after the short page rather than requesting a 3rd page
    assert len(commits) == 101
