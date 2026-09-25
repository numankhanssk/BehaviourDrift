"""
backend/main.py — FastAPI backend for BehaviorDrift.

Wraps the exact same run_pipeline / run_pipeline_from_synthetic functions that
demo/run_demo.py and tests/ already exercise. No pipeline, detector, agent,
memory, vectorizer, or collector logic is touched or duplicated here.

Expected layout :

    your-project/
    ├── .env
    ├── requirements.txt
    ├── data/
    │   └── local_memory.json
    ├── demo/
    │   └── run_demo.py
    ├── src/
    │   ├── agent.py
    │   ├── collector.py
    │   ├── detector.py
    │   ├── detector_ml.py
    │   ├── memory.py
    │   ├── pipeline.py
    │   ├── report.py
    │   └── vectorizer.py
    ├── tests/
    ├── backend/
    │   ├── main.py          <- this file
    │   └── requirements.txt
    └── frontend/            <- React app

Run locally:
    cd backend
    pip install -r requirements.txt
    uvicorn main:app --reload --port 8000
"""

import os
import sys

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# backend/main.py -> project root is one level up, same as app.py's sys.path insert
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

load_dotenv()

from src.pipeline import run_pipeline, run_pipeline_from_synthetic  # noqa: E402

app = FastAPI(title="BehaviorDrift API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=os.environ.get("CORS_ORIGINS", "http://localhost:5173").split(","),
    allow_methods=["*"],
    allow_headers=["*"],
)

SYNTHETIC_SAMPLE = {
    "2026-W16": {"commit_count": 10, "authors": {"a", "b", "c"}, "dependency_touches": 0},
    "2026-W17": {"commit_count": 11, "authors": {"a", "b", "c"}, "dependency_touches": 0},
    "2026-W18": {"commit_count": 9,  "authors": {"a", "b"},      "dependency_touches": 1},
    "2026-W19": {"commit_count": 12, "authors": {"a", "b", "c"}, "dependency_touches": 0},
    "2026-W20": {"commit_count": 40, "authors": {"a"},           "dependency_touches": 6},
}


class GithubScanRequest(BaseModel):
    owner: str
    repo: str


@app.get("/api/backend-status")
def backend_status():

    if os.environ.get("ANTHROPIC_API_KEY"):
        return {"backend": "claude", "label": "Claude", "detail": "ANTHROPIC_API_KEY set"}
    if os.environ.get("GEMINI_API_KEY"):
        return {
            "backend": "gemini",
            "label": "Gemini",
            "detail": "unverified integration, see README",
        }
    return {
        "backend": "template",
        "label": "Template fallback",
        "detail": "set ANTHROPIC_API_KEY or GEMINI_API_KEY for real LLM explanations",
    }


@app.post("/api/scan/sample")
def scan_sample():
    result = run_pipeline_from_synthetic("demo/synthetic-repo", SYNTHETIC_SAMPLE)
    if "error" in result:
        raise HTTPException(status_code=422, detail=result["error"])
    return result


@app.post("/api/scan/github")
def scan_github(payload: GithubScanRequest):
    if not payload.owner or not payload.repo:
        raise HTTPException(status_code=400, detail="Enter a repo as owner/repo, e.g. pallets/flask")
    try:
        result = run_pipeline(payload.owner, payload.repo)
    except Exception as e:
        raise HTTPException(
            status_code=502,
            detail=(
                f"Pipeline failed: {e}. If this is a rate-limit error, set a GITHUB_TOKEN "
                "environment variable — the public API allows only ~60 requests/hour without one."
            ),
        )
    if "error" in result:
        raise HTTPException(status_code=422, detail=result["error"])
    return result
