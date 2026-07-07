"""RM Copilot endpoint — Claude tool-use agent."""
from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ...agents.copilot import ask_copilot
from ...db import get_session
from ...models.prospect import Prospect
from ...models.interaction_log import ProspectInteractionLog
from ...scoring.scorer import compute_lead_score
from ...scoring.weights import SCORE_VERSION

router = APIRouter(prefix="/copilot", tags=["copilot"])


class CopilotRequest(BaseModel):
    question: str
    rm_id: str = ""


class CopilotResponse(BaseModel):
    answer: str
    model_used: str


@router.post("/ask", response_model=CopilotResponse)
def ask(body: CopilotRequest, session: Session = Depends(get_session)):
    prospects = session.query(Prospect).all()

    prospect_lookup = {p.prospect_id: {
        "prospect_id": p.prospect_id, "name": p.name,
        "lead_score": p.lead_score, "lead_band": p.lead_band,
        "recommended_product": p.recommended_product,
        "recommended_channel": p.recommended_channel,
        "recommended_timing": p.recommended_timing,
        "segment": p.segment, "annual_income": p.annual_income,
        "existing_customer": p.existing_customer,
        "digital_activity_score": p.digital_activity_score,
        "last_interaction_days": p.last_interaction_days,
        "life_event": p.life_event,
        "credit_bureau_score": p.credit_bureau_score,
        "loan_enquiries_6m": p.loan_enquiries_6m,
    } for p in prospects}

    contribution_lookup: dict[str, list] = {}
    for p in prospects:
        raw = {k: prospect_lookup[p.prospect_id][k] for k in [
            "prospect_id", "segment", "annual_income", "existing_customer",
            "digital_activity_score", "last_interaction_days", "life_event",
            "credit_bureau_score", "loan_enquiries_6m",
        ]}
        result = compute_lead_score(raw)
        contribution_lookup[p.prospect_id] = [
            {"component": c.component, "contribution": c.contribution, "description": c.description}
            for c in result.contributions
        ]

    from ...config import get_settings
    settings = get_settings()
    model_used = settings.copilot_model if settings.anthropic_api_key else "rule-based-fallback"

    answer = ask_copilot(body.question, prospect_lookup, contribution_lookup)

    # Log the copilot interaction
    for pid in prospect_lookup:
        if pid.lower() in body.question.lower():
            session.add(ProspectInteractionLog(
                prospect_id=pid, rm_id=body.rm_id,
                event_type="copilot_query",
                event_detail=body.question[:500],
                lead_score_snapshot=prospect_lookup[pid]["lead_score"],
                score_version=SCORE_VERSION,
            ))
    session.commit()

    return CopilotResponse(answer=answer, model_used=model_used)
