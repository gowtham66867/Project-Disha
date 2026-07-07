"""Deterministic lead scoring engine with SHAP-style contribution breakdown.

Each component contributes to the 0-100 score with a signed contribution
so RMs and regulators can see exactly why a prospect scored X.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from .weights import (
    BAND_THRESHOLDS, LIFE_EVENT_BOOST, NBA_CHANNEL, NBA_PRODUCT,
    NBA_TIMING, SCORE_VERSION, WEIGHTS,
)


@dataclass
class ScoreContribution:
    component: str
    raw_value: float
    contribution: float  # signed points contributed to final score
    description: str


@dataclass
class LeadScoreResult:
    prospect_id: str
    lead_score: float
    lead_band: str
    recommended_product: str
    recommended_channel: str
    recommended_timing: str
    contributions: list[ScoreContribution] = field(default_factory=list)
    score_version: str = SCORE_VERSION


def _band(score: float) -> str:
    for threshold, label in BAND_THRESHOLDS:
        if score >= threshold:
            return label
    return "Cold"


def _nba_product(segment: str, life_event: Optional[str]) -> str:
    segment_map = NBA_PRODUCT.get(segment, NBA_PRODUCT.get("Salaried", {}))
    if life_event and life_event in segment_map:
        return segment_map[life_event]
    return segment_map.get("default", "Standard Banking Products")


def compute_lead_score(p: dict) -> LeadScoreResult:
    contributions: list[ScoreContribution] = []

    # 1. Credit bureau score (300-900 range → 0-25 pts)
    bureau = p.get("credit_bureau_score", 650)
    bureau_pts = max(0.0, min(25.0, (bureau - 600) / 12.0))
    contributions.append(ScoreContribution(
        "credit_bureau", bureau, round(bureau_pts, 2),
        f"Bureau score {bureau} → {round(bureau_pts, 1)} pts",
    ))

    # 2. Annual income (log-scaled → 0-20 pts)
    import math
    income = max(1, p.get("annual_income", 500000))
    income_pts = min(20.0, math.log10(income / 100000) * 8.0)
    income_pts = max(0.0, income_pts)
    contributions.append(ScoreContribution(
        "income", income, round(income_pts, 2),
        f"Income ₹{income:,.0f} → {round(income_pts, 1)} pts",
    ))

    # 3. Digital activity (0-100 raw → 0-15 pts)
    digital = p.get("digital_activity_score", 50)
    digital_pts = digital * 0.15
    contributions.append(ScoreContribution(
        "digital_activity", digital, round(digital_pts, 2),
        f"Digital score {digital}/100 → {round(digital_pts, 1)} pts",
    ))

    # 4. Life event boost (0-15 pts)
    life_event = p.get("life_event") or ""
    le_pts = LIFE_EVENT_BOOST.get(life_event, 0.0)
    contributions.append(ScoreContribution(
        "life_event", 1.0 if life_event else 0.0, le_pts,
        f"Life event '{life_event}' → {le_pts} pts" if life_event else "No life event → 0 pts",
    ))

    # 5. Recency of last interaction (0-10 pts; fresher = higher)
    days = p.get("last_interaction_days", 30)
    recency_pts = max(0.0, 10.0 - days * 0.15)
    contributions.append(ScoreContribution(
        "recency", days, round(recency_pts, 2),
        f"Last contact {days} days ago → {round(recency_pts, 1)} pts",
    ))

    # 6. Existing customer bonus (0 or 10 pts)
    existing = p.get("existing_customer", False)
    existing_pts = 10.0 if existing else 0.0
    contributions.append(ScoreContribution(
        "existing_customer", float(existing), existing_pts,
        "Existing customer → 10 pts" if existing else "New prospect → 0 pts",
    ))

    # 7. Enquiry penalty (0 to -5 pts)
    enquiries = p.get("loan_enquiries_6m", 0)
    enq_penalty = -min(5.0, enquiries * 1.5)
    contributions.append(ScoreContribution(
        "enquiry_penalty", enquiries, round(enq_penalty, 2),
        f"{enquiries} loan enquiries in 6m → {round(enq_penalty, 1)} pts",
    ))

    raw_score = sum(c.contribution for c in contributions)
    final_score = round(max(0.0, min(100.0, raw_score)), 2)
    band = _band(final_score)

    return LeadScoreResult(
        prospect_id=p.get("prospect_id", ""),
        lead_score=final_score,
        lead_band=band,
        recommended_product=_nba_product(p.get("segment", "Salaried"), life_event or None),
        recommended_channel=NBA_CHANNEL[band],
        recommended_timing=NBA_TIMING[band],
        contributions=contributions,
        score_version=SCORE_VERSION,
    )
