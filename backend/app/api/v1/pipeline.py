"""Pipeline analytics — funnel summary and RM leaderboard."""
from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import func
from sqlalchemy.orm import Session

from ...db import get_session
from ...models.prospect import Prospect

router = APIRouter(prefix="/pipeline", tags=["pipeline"])


class BandSummary(BaseModel):
    band: str
    count: int
    avg_score: float


class StageSummary(BaseModel):
    stage: str
    count: int


class PipelineStats(BaseModel):
    total: int
    by_band: list[BandSummary]
    by_stage: list[StageSummary]
    avg_score: float
    hot_prospects: int


@router.get("/stats", response_model=PipelineStats)
def pipeline_stats(session: Session = Depends(get_session)):
    all_p = session.query(Prospect).all()
    total = len(all_p)
    avg_score = sum(p.lead_score for p in all_p) / total if total else 0

    band_map: dict[str, list[float]] = {}
    stage_map: dict[str, int] = {}
    for p in all_p:
        band_map.setdefault(p.lead_band, []).append(p.lead_score)
        stage_map[p.pipeline_stage] = stage_map.get(p.pipeline_stage, 0) + 1

    by_band = [
        BandSummary(band=b, count=len(scores), avg_score=round(sum(scores) / len(scores), 1))
        for b, scores in sorted(band_map.items(), key=lambda x: -sum(x[1]))
    ]
    by_stage = [StageSummary(stage=s, count=c) for s, c in stage_map.items()]

    return PipelineStats(
        total=total,
        by_band=by_band,
        by_stage=by_stage,
        avg_score=round(avg_score, 1),
        hot_prospects=sum(1 for p in all_p if p.lead_band == "Hot"),
    )
