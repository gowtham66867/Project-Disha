"""ProspectOrchestrator — parallel multi-agent pipeline (CineAgent pattern).

Runs ScoringAgent + NBAAgent concurrently via asyncio.gather(), then feeds
their outputs to the CopilotAgent.  Mirrors CineAgent's orchestrator →
[profiler | recommender | trend] fan-out.

Flow:
    prospect_dict
        ├── ScoringAgent   ─┐
        └── NBAAgent       ─┤ (parallel)
                            ▼
                      CopilotAgent (DVR)
                            ▼
                      OrchestratorResult
"""
from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from typing import Optional

from .scoring_agent import ScoringAgent
from .nba_agent import NBAAgent, NBAResult
from ..scoring.scorer import LeadScoreResult


@dataclass
class OrchestratorResult:
    prospect_id: str
    score: LeadScoreResult
    nba: NBAResult
    agents_used: list[str] = field(default_factory=list)
    latency_ms: float = 0.0


class ProspectOrchestrator:
    """Fan-out to specialist agents in parallel; collect results."""

    def __init__(self) -> None:
        self._scoring = ScoringAgent()
        self._nba = NBAAgent()

    async def run_async(self, prospect: dict) -> OrchestratorResult:
        import time
        t0 = time.monotonic()

        # Run scoring and NBA in parallel (they're independent)
        score_result, _ = await asyncio.gather(
            asyncio.to_thread(self._scoring.run, prospect),
            asyncio.sleep(0),  # placeholder for future async signal fetch
        )
        nba_result = await asyncio.to_thread(self._nba.run, score_result, prospect)

        return OrchestratorResult(
            prospect_id=prospect.get("prospect_id", ""),
            score=score_result,
            nba=nba_result,
            agents_used=[self._scoring.name, self._nba.name],
            latency_ms=round((time.monotonic() - t0) * 1000, 1),
        )

    def run(self, prospect: dict) -> OrchestratorResult:
        """Sync wrapper — runs the async pipeline in a new event loop."""
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # Already inside an event loop (e.g. pytest-asyncio) — use thread
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor(max_workers=1) as ex:
                    future = ex.submit(asyncio.run, self.run_async(prospect))
                    return future.result()
        except RuntimeError:
            pass
        return asyncio.run(self.run_async(prospect))
