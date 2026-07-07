"""Lead score detail — contributions breakdown for a prospect."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ...db import get_session
from ...models.prospect import Prospect
from ...scoring.scorer import compute_lead_score

router = APIRouter(prefix="/score", tags=["score"])


class Contribution(BaseModel):
    component: str
    raw_value: float
    contribution: float
    description: str


class ScoreDetail(BaseModel):
    prospect_id: str
    lead_score: float
    lead_band: str
    score_version: str
    contributions: list[Contribution]


@router.get("/{prospect_id}", response_model=ScoreDetail)
def score_detail(prospect_id: str, session: Session = Depends(get_session)):
    p = session.get(Prospect, prospect_id)
    if not p:
        raise HTTPException(status_code=404, detail="Prospect not found")
    raw = {
        "prospect_id": p.prospect_id, "segment": p.segment,
        "annual_income": p.annual_income, "existing_customer": p.existing_customer,
        "digital_activity_score": p.digital_activity_score,
        "last_interaction_days": p.last_interaction_days,
        "life_event": p.life_event, "credit_bureau_score": p.credit_bureau_score,
        "loan_enquiries_6m": p.loan_enquiries_6m,
    }
    result = compute_lead_score(raw)
    return ScoreDetail(
        prospect_id=prospect_id,
        lead_score=result.lead_score,
        lead_band=result.lead_band,
        score_version=result.score_version,
        contributions=[
            Contribution(
                component=c.component,
                raw_value=c.raw_value,
                contribution=c.contribution,
                description=c.description,
            )
            for c in result.contributions
        ],
    )
