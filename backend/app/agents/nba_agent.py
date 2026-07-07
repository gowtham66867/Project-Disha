"""NBAAgent — derives Next Best Action from a score result and prospect profile."""
from __future__ import annotations

from dataclasses import dataclass

from ..scoring.scorer import LeadScoreResult
from ..scoring.weights import NBA_CHANNEL, NBA_TIMING


@dataclass
class NBAResult:
    prospect_id: str
    recommended_product: str
    recommended_channel: str
    recommended_timing: str
    priority_reason: str


class NBAAgent:
    name = "nba_agent"

    def run(self, score: LeadScoreResult, prospect: dict) -> NBAResult:
        top = max(score.contributions, key=lambda c: c.contribution)
        reason = f"Top driver: {top.component.replace('_', ' ')} ({top.description})"

        return NBAResult(
            prospect_id=score.prospect_id,
            recommended_product=score.recommended_product,
            recommended_channel=score.recommended_channel,
            recommended_timing=score.recommended_timing,
            priority_reason=reason,
        )
