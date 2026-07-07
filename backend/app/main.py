"""Project Disha — Prospect Assist AI for IDBI Bank."""
from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .db import init_db, SessionLocal
from .seed.loader import seed
from .config import get_settings
from .api.v1 import prospects, score, copilot, pipeline

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
    description="AI-powered lead scoring and RM copilot for IDBI Bank (IDBI Innovate 2026, PS-2)",
    version="1.0.0",
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


@app.get("/health")
def health():
    return {"status": "ok", "service": "project-disha"}
