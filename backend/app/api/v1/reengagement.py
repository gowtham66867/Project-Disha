"""Re-engagement API — ColdProspectReEngagementAgent endpoints."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ...agents.reengagement import ColdProspectReEngagementAgent, ReEngagementCandidate
from ...db import get_session
from ...models.prospect import Prospect
from ...models.interaction_log import ProspectInteractionLog
from ...scoring.weights import SCORE_VERSION

router = APIRouter(prefix="/reengagement", tags=["reengagement"])
_agent = ColdProspectReEngagementAgent()


class CandidateOut(BaseModel):
    prospect_id: str
    name: str
    segment: str
    lead_band: str
    lead_score: float
    life_event: str
    recommended_product: str
    days_since_contact: int
    urgency_score: int
    whatsapp_script: str
    sms_script: str


class SendResult(BaseModel):
    status: str
    prospect_id: str
    message: str = ""


def _prospect_to_dict(p: Prospect) -> dict:
    return {
        "prospect_id": p.prospect_id, "name": p.name, "segment": p.segment,
        "lead_band": p.lead_band, "lead_score": p.lead_score,
        "life_event": p.life_event, "recommended_product": p.recommended_product,
        "last_interaction_days": p.last_interaction_days,
        "existing_customer": p.existing_customer,
    }


@router.get("/candidates", response_model=list[CandidateOut])
def get_candidates(top_n: int = 5, session: Session = Depends(get_session)):
    """Return top cold/lukewarm prospects ranked by re-engagement urgency."""
    prospects = [_prospect_to_dict(p) for p in session.query(Prospect).all()]
    candidates = _agent.find_candidates(prospects, top_n=top_n)
    return [CandidateOut(**vars(c)) for c in candidates]


@router.post("/send/{prospect_id}", response_model=SendResult)
def send_nudge(prospect_id: str, session: Session = Depends(get_session)):
    """Dispatch WhatsApp/SMS nudge for a cold prospect via CPaaS."""
    p = session.get(Prospect, prospect_id)
    if not p:
        raise HTTPException(status_code=404, detail="Prospect not found")

    candidates = _agent.find_candidates([_prospect_to_dict(p)], top_n=1)
    if not candidates:
        raise HTTPException(status_code=422, detail="Prospect is not in a cold/lukewarm band")

    result = _agent.send(candidates[0])

    session.add(ProspectInteractionLog(
        prospect_id=prospect_id, rm_id="system",
        event_type="reengagement_nudge_sent",
        event_detail=candidates[0].sms_script,
        lead_score_snapshot=p.lead_score,
        score_version=SCORE_VERSION,
    ))
    session.commit()

    return SendResult(
        status=result["status"],
        prospect_id=prospect_id,
        message=candidates[0].sms_script,
    )
