"""60's Pulse FastAPI server.

Rung 0: serve the broadsheet dashboard (static) + the baked golden run.
The dashboard is a pure render of /api/golden, so nothing here calls a sponsor API.
Run:  uvicorn app.main:app --reload  (from the repo root, with the venv active)
"""
import json
import os
from typing import Literal

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, ConfigDict, Field

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATIC_DIR = os.path.join(ROOT, "app", "static")
GOLDEN_PATH = os.path.join(ROOT, "golden", "golden_run.json")

try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(ROOT, ".env"))  # so live /api/analyze has the API keys
except ImportError:
    pass

app = FastAPI(title="60's Pulse", version="0.1.0")


class AnalyzeRequest(BaseModel):
    model_config = ConfigDict(frozen=True)

    campaign: str
    brand: str = ""
    provider: Literal["kimi", "openai"] = "kimi"
    brightdata: bool = False
    daytona: bool = False
    videodb: bool = False
    video_source: str = ""
    allow_baked_grounding: bool = False
    sandbox_limit: int = Field(default=0, ge=0)


@app.get("/healthz")
def healthz():
    return {"ok": True, "mode": "fixture"}


@app.get("/api/golden")
def api_golden():
    """The single object the dashboard renders. Rung 0 = baked fixture."""
    with open(GOLDEN_PATH, encoding="utf-8") as f:
        return JSONResponse(json.load(f))


@app.post("/api/analyze")
async def api_analyze(payload: AnalyzeRequest):
    """Live 'paste your own campaign' path: regenerate the 60-agent panel for the typed input."""
    campaign = payload.campaign.strip()
    if not campaign:
        raise HTTPException(status_code=400, detail="campaign text required")
    brand = payload.brand.strip() or "the brand"
    video_source = payload.video_source.strip()
    if payload.videodb and not video_source:
        raise HTTPException(status_code=400, detail="video_source required when videodb is enabled")
    from app.analyze import AnalyzeInput, AnalyzeOptions, analyze
    with open(GOLDEN_PATH, encoding="utf-8") as f:
        golden = json.load(f)
    try:
        result = await analyze(
            AnalyzeInput(campaign=campaign, brand=brand, golden=golden, video_source=video_source),
            AnalyzeOptions(
                provider=payload.provider,
                mode="live",
                brightdata=payload.brightdata,
                daytona=payload.daytona,
                videodb=payload.videodb,
                allow_baked_grounding=payload.allow_baked_grounding,
                sandbox_limit=payload.sandbox_limit,
            ),
        )
    except RuntimeError as e:
        return JSONResponse({"detail": f"{type(e).__name__}: {e}"}, status_code=502)
    return JSONResponse(result)


# Mount the dashboard last so the explicit /api routes win.
app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="static")
