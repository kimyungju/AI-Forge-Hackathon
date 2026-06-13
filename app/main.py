"""Premortem FastAPI server.

Rung 0: serve the broadsheet dashboard (static) + the baked golden run.
The dashboard is a pure render of /api/golden, so nothing here calls a sponsor API.
Run:  uvicorn app.main:app --reload  (from the repo root, with the venv active)
"""
import json
import os

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATIC_DIR = os.path.join(ROOT, "app", "static")
GOLDEN_PATH = os.path.join(ROOT, "golden", "golden_run.json")

app = FastAPI(title="Premortem", version="0.1.0")


@app.get("/healthz")
def healthz():
    return {"ok": True, "mode": "fixture"}


@app.get("/api/golden")
def api_golden():
    """The single object the dashboard renders. Rung 0 = baked fixture."""
    with open(GOLDEN_PATH, encoding="utf-8") as f:
        return JSONResponse(json.load(f))


@app.post("/api/analyze")
def api_analyze():
    """Rung 1+: the real collect -> sandbox -> panel -> reduce pipeline. Not built yet."""
    return JSONResponse(
        {"detail": "analyze pipeline lands in Rung 1; the demo replays /api/golden"},
        status_code=501,
    )


# Mount the dashboard last so the explicit /api routes win.
app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="static")
