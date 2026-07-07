"""RM Copilot endpoint — multi-provider DVR agent with episodic memory."""
from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ...agents.copilot import ask_copilot
from ...db import get_session
from ...config import get_settings
from ...models.prospect import Prospect
from ...models.interaction_log import ProspectInteractionLog
from ...models.copilot_memory import CopilotMemory
from ...scoring.scorer import compute_lead_score
from ...scoring.weights import SCORE_VERSION

router = APIRouter(prefix="/copilot", tags=["copilot"])
settings = get_settings()

_MEMORY_WINDOW = 6  # inject last N turns as context


class CopilotRequest(BaseModel):
    question: str
    rm_id: str = ""
    prospect_id: str = ""   # optional focus prospect


class CopilotResponse(BaseModel):
    answer: str
    provider: str
    memory_turns_used: int


class MemoryEntry(BaseModel):
    role: str
    content: str
    created_at: str


class MemoryHistory(BaseModel):
    prospect_id: str
    history: list[MemoryEntry]


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

    # --- Episodic memory: load last N turns ---
    pid = body.prospect_id
    history_rows = (
        session.query(CopilotMemory)
        .filter(CopilotMemory.prospect_id == pid)
        .order_by(CopilotMemory.created_at.desc())
        .limit(_MEMORY_WINDOW)
        .all()
    ) if pid else []
    history_rows = list(reversed(history_rows))
    history = [{"role": r.role, "content": r.content} for r in history_rows]

    # --- Run copilot (DVR + multi-provider) ---
    answer, provider = ask_copilot(
        question=body.question,
        prospect_lookup=prospect_lookup,
        contribution_lookup=contribution_lookup,
        history=history,
        anthropic_api_key=settings.anthropic_api_key,
        gemini_api_key=settings.gemini_api_key,
        claude_model=settings.copilot_model,
    )

    # --- Persist to episodic memory ---
    if pid:
        session.add(CopilotMemory(prospect_id=pid, rm_id=body.rm_id, role="user", content=body.question, provider=""))
        session.add(CopilotMemory(prospect_id=pid, rm_id=body.rm_id, role="assistant", content=answer, provider=provider))

    # Log to interaction audit
    for p_id in prospect_lookup:
        if p_id.lower() in body.question.lower():
            session.add(ProspectInteractionLog(
                prospect_id=p_id, rm_id=body.rm_id,
                event_type="copilot_query",
                event_detail=body.question[:500],
                lead_score_snapshot=prospect_lookup[p_id]["lead_score"],
                score_version=SCORE_VERSION,
            ))
    session.commit()

    return CopilotResponse(answer=answer, provider=provider, memory_turns_used=len(history))


@router.get("/history/{prospect_id}", response_model=MemoryHistory)
def memory_history(prospect_id: str, session: Session = Depends(get_session)):
    rows = (
        session.query(CopilotMemory)
        .filter(CopilotMemory.prospect_id == prospect_id)
        .order_by(CopilotMemory.created_at.asc())
        .all()
    )
    return MemoryHistory(
        prospect_id=prospect_id,
        history=[
            MemoryEntry(role=r.role, content=r.content, created_at=str(r.created_at))
            for r in rows
        ],
    )
