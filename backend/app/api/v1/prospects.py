"""Prospect pipeline API."""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ...db import get_session
from ...models.prospect import Prospect
from ...models.interaction_log import ProspectInteractionLog
from ...scoring.scorer import compute_lead_score
from ...scoring.weights import SCORE_VERSION

router = APIRouter(prefix="/prospects", tags=["prospects"])


class ProspectOut(BaseModel):
    prospect_id: str
    name: str
    age: int
    city: str
    state: str
    segment: str
    annual_income: float
    existing_customer: bool
    life_event: str
    lead_score: float
    lead_band: str
    recommended_product: str
    recommended_channel: str
    recommended_timing: str
    pipeline_stage: str
    rm_id: str
    score_version: str

    model_config = {"from_attributes": True}


class StageUpdate(BaseModel):
    stage: str


@router.get("/", response_model=list[ProspectOut])
def list_prospects(
    rm_id: Optional[str] = Query(None),
    band: Optional[str] = Query(None),
    stage: Optional[str] = Query(None),
    session: Session = Depends(get_session),
):
    q = session.query(Prospect)
    if rm_id:
        q = q.filter(Prospect.rm_id == rm_id)
    if band:
        q = q.filter(Prospect.lead_band == band)
    if stage:
        q = q.filter(Prospect.pipeline_stage == stage)
    return q.order_by(Prospect.lead_score.desc()).all()


@router.get("/{prospect_id}", response_model=ProspectOut)
def get_prospect(prospect_id: str, session: Session = Depends(get_session)):
    p = session.get(Prospect, prospect_id)
    if not p:
        raise HTTPException(status_code=404, detail="Prospect not found")
    return p


@router.post("/{prospect_id}/rescore", response_model=ProspectOut)
def rescore_prospect(prospect_id: str, session: Session = Depends(get_session)):
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
    p.lead_score = result.lead_score
    p.lead_band = result.lead_band
    p.recommended_product = result.recommended_product
    p.recommended_channel = result.recommended_channel
    p.recommended_timing = result.recommended_timing
    p.score_version = result.score_version
    session.add(ProspectInteractionLog(
        prospect_id=prospect_id, rm_id=p.rm_id,
        event_type="score_computed",
        event_detail=f"Rescored: {result.lead_score:.1f} ({result.lead_band})",
        lead_score_snapshot=result.lead_score,
        score_version=SCORE_VERSION,
    ))
    session.commit()
    session.refresh(p)
    return p


@router.patch("/{prospect_id}/stage", response_model=ProspectOut)
def update_stage(
    prospect_id: str,
    body: StageUpdate,
    session: Session = Depends(get_session),
):
    valid_stages = {"New", "Contacted", "Interested", "Proposal Sent", "Won", "Lost"}
    if body.stage not in valid_stages:
        raise HTTPException(status_code=422, detail=f"stage must be one of {sorted(valid_stages)}")
    p = session.get(Prospect, prospect_id)
    if not p:
        raise HTTPException(status_code=404, detail="Prospect not found")
    p.pipeline_stage = body.stage
    session.add(ProspectInteractionLog(
        prospect_id=prospect_id, rm_id=p.rm_id,
        event_type="stage_changed",
        event_detail=f"Stage → {body.stage}",
        lead_score_snapshot=p.lead_score,
        score_version=p.score_version,
    ))
    session.commit()
    session.refresh(p)
    return p
