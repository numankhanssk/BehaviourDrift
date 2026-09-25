"""
run_demo.py — CLI entrypoint.

Usage:
  python demo/run_demo.py --offline                 # synthetic data, no network needed
  python demo/run_demo.py --repo pallets/flask       # live GitHub repo (needs GITHUB_TOKEN
                                                      # if you're past the 60/hr anonymous limit)
"""

import sys
import os
import argparse
import json

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.pipeline import run_pipeline, run_pipeline_from_synthetic
from src.report import save_html_report


SYNTHETIC_SAMPLE = {
    "2026-W16": {"commit_count": 10, "authors": {"a", "b", "c"}, "dependency_touches": 0},
    "2026-W17": {"commit_count": 11, "authors": {"a", "b", "c"}, "dependency_touches": 0},
    "2026-W18": {"commit_count": 9,  "authors": {"a", "b"},      "dependency_touches": 1},
    "2026-W19": {"commit_count": 12, "authors": {"a", "b", "c"}, "dependency_touches": 0},
    "2026-W20": {"commit_count": 40, "authors": {"a"},           "dependency_touches": 6},
}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", help="owner/repo, e.g. pallets/flask")
    parser.add_argument("--offline", action="store_true", help="use synthetic data, no GitHub API calls")
    parser.add_argument("--out", default="report.html", help="output HTML path")
    args = parser.parse_args()

    if args.offline or not args.repo:
        print("[demo] Running on synthetic data (offline mode)...")
        report = run_pipeline_from_synthetic("demo/synthetic-repo", SYNTHETIC_SAMPLE)
    else:
        owner, repo = args.repo.split("/")
        print(f"[demo] Running live pipeline against {args.repo}...")
        report = run_pipeline(owner, repo)

    print(json.dumps(report["summary"], indent=2))
    path = save_html_report(report, args.out)
    print(f"[demo] HTML report written to {path}")


if __name__ == "__main__":
    main()
