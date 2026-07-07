from __future__ import annotations

from sqlalchemy.orm import Session

from ..adapters import get_adapter
from ..models.prospect import Prospect
from ..scoring.scorer import compute_lead_score


def seed(session: Session, seed_path: str = "") -> int:
    if session.query(Prospect).count() > 0:
        return 0

    adapter = get_adapter(seed_path)
    records = adapter.fetch_all()
    count = 0
    for raw in records:
        result = compute_lead_score(raw)
        life_event = raw.get("life_event") or ""
        p = Prospect(
            prospect_id=raw["prospect_id"],
            name=raw.get("name", ""),
            age=raw.get("age", 0),
            city=raw.get("city", ""),
            state=raw.get("state", ""),
            segment=raw.get("segment", "Salaried"),
            annual_income=raw.get("annual_income", 0),
            existing_customer=raw.get("existing_customer", False),
            digital_activity_score=raw.get("digital_activity_score", 0),
            last_interaction_days=raw.get("last_interaction_days", 0),
            life_event=life_event,
            credit_bureau_score=raw.get("credit_bureau_score", 650),
            employer_category=raw.get("employer_category", ""),
            loan_enquiries_6m=raw.get("loan_enquiries_6m", 0),
            upi_monthly_txn=raw.get("upi_monthly_txn", 0),
            rm_id=raw.get("rm_id", ""),
            lead_score=result.lead_score,
            lead_band=result.lead_band,
            recommended_product=result.recommended_product,
            recommended_channel=result.recommended_channel,
            recommended_timing=result.recommended_timing,
            score_version=result.score_version,
            pipeline_stage="New",
        )
        session.add(p)
        count += 1
    session.commit()
    return count
