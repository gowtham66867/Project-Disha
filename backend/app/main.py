"""Project Disha — Prospect Assist AI for IDBI Bank."""
from __future__ import annotations

from contextlib import asynccontextmanager

import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse, FileResponse
from fastapi.staticfiles import StaticFiles

from .db import init_db, SessionLocal
from .seed.loader import seed
from .config import get_settings
from .api.v1 import prospects, score, copilot, pipeline, reengagement

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    with SessionLocal() as s:
        n = seed(s, settings.seed_file)
        if n:
            print(f"[disha] seeded {n} prospects")
    yield


app = FastAPI(
    title="Project Disha — Prospect Assist AI",
    description=(
        "AI-powered lead scoring and RM copilot for IDBI Bank (IDBI Innovate 2026, PS-2). "
        "Multi-agent orchestration · DVR loop · Episodic memory · Multi-provider LLM governance."
    ),
    version="2.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(prospects.router, prefix="/api/v1")
app.include_router(score.router, prefix="/api/v1")
app.include_router(copilot.router, prefix="/api/v1")
app.include_router(pipeline.router, prefix="/api/v1")
app.include_router(reengagement.router, prefix="/api/v1")


@app.get("/health")
def health():
    return {"status": "ok", "service": "project-disha", "version": "2.0.0"}


# Serve React frontend from /static dir (built by Dockerfile multi-stage)
_STATIC = os.path.join(os.path.dirname(__file__), "..", "static")
if os.path.isdir(_STATIC):
    app.mount("/assets", StaticFiles(directory=os.path.join(_STATIC, "assets")), name="assets")

    @app.get("/", include_in_schema=False)
    @app.get("/{full_path:path}", include_in_schema=False)
    def spa(full_path: str = ""):
        if full_path.startswith(("api/", "docs", "redoc", "openapi", "health")):
            from fastapi import HTTPException
            raise HTTPException(status_code=404)
        return FileResponse(os.path.join(_STATIC, "index.html"))
else:
    @app.get("/", include_in_schema=False)
    def root():
        return RedirectResponse(url="/docs")
