"""ScoringAgent — computes lead score and contributions for a prospect dict."""
from __future__ import annotations

from ..scoring.scorer import LeadScoreResult, compute_lead_score


class ScoringAgent:
    name = "scoring_agent"

    def run(self, prospect_dict: dict) -> LeadScoreResult:
        return compute_lead_score(prospect_dict)
