"""Tests for multi-agent orchestration, reengagement agent, and episodic memory."""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.agents.orchestrator import ProspectOrchestrator
from app.agents.reengagement import ColdProspectReEngagementAgent
from app.agents.llm_provider import LLMGovernor

PROSPECT = {
    "prospect_id": "TEST001",
    "segment": "Salaried",
    "annual_income": 1200000,
    "existing_customer": False,
    "digital_activity_score": 70,
    "last_interaction_days": 5,
    "life_event": "home_purchase",
    "credit_bureau_score": 740,
    "loan_enquiries_6m": 1,
    "lead_band": "Warm",
    "lead_score": 58.0,
    "name": "Test User",
    "recommended_product": "Home Loan",
}

COLD_PROSPECT = {**PROSPECT, "prospect_id": "COLD001", "lead_band": "Cold",
                 "lead_score": 20.0, "last_interaction_days": 45, "life_event": "home_purchase"}


# ── Orchestrator ──────────────────────────────────────────────────────────────

def test_orchestrator_returns_score_and_nba():
    orch = ProspectOrchestrator()
    result = orch.run(PROSPECT)
    assert result.score.lead_score > 0
    assert result.nba.recommended_product != ""
    assert "scoring_agent" in result.agents_used
    assert "nba_agent" in result.agents_used


def test_orchestrator_latency_recorded():
    orch = ProspectOrchestrator()
    result = orch.run(PROSPECT)
    assert result.latency_ms >= 0


def test_orchestrator_score_matches_direct():
    from app.scoring.scorer import compute_lead_score
    orch = ProspectOrchestrator()
    orch_score = orch.run(PROSPECT).score.lead_score
    direct_score = compute_lead_score(PROSPECT).lead_score
    assert orch_score == direct_score


# ── ReEngagement Agent ────────────────────────────────────────────────────────

def test_reengagement_finds_cold_prospects():
    agent = ColdProspectReEngagementAgent()
    prospects = [PROSPECT, COLD_PROSPECT]
    candidates = agent.find_candidates(prospects)
    assert any(c.prospect_id == "COLD001" for c in candidates)


def test_reengagement_warm_not_returned():
    agent = ColdProspectReEngagementAgent()
    warm = {**PROSPECT, "lead_band": "Hot"}
    candidates = agent.find_candidates([warm])
    assert len(candidates) == 0


def test_reengagement_scripts_non_empty():
    agent = ColdProspectReEngagementAgent()
    candidates = agent.find_candidates([COLD_PROSPECT])
    assert len(candidates) == 1
    assert len(candidates[0].whatsapp_script) > 50
    assert len(candidates[0].sms_script) > 20


def test_reengagement_urgency_with_life_event():
    agent = ColdProspectReEngagementAgent()
    with_event = {**COLD_PROSPECT, "life_event": "home_purchase"}
    without_event = {**COLD_PROSPECT, "life_event": None}
    c1 = agent.find_candidates([with_event])
    c2 = agent.find_candidates([without_event])
    assert c1[0].urgency_score >= c2[0].urgency_score


# ── LLM Governor (rule-based path) ───────────────────────────────────────────

def test_llm_governor_rule_based_fallback():
    gov = LLMGovernor()  # no keys → rule-based
    resp = gov.complete(
        system="You are a banking AI.",
        messages=[{"role": "user", "content": "Who should I call today?"}],
    )
    assert resp.provider == "rule_based"
    assert len(resp.text) > 10


# ── API endpoints ─────────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


def test_reengagement_candidates_api(client):
    resp = client.get("/api/v1/reengagement/candidates")
    assert resp.status_code == 200
    body = resp.json()
    assert isinstance(body, list)
    # All returned candidates should be in cold bands
    for c in body:
        assert c["lead_band"] in ("Cold", "Lukewarm")


def test_copilot_memory_history_empty(client):
    resp = client.get("/api/v1/copilot/history/NOBODY")
    assert resp.status_code == 200
    assert resp.json()["history"] == []


def test_copilot_ask_returns_provider(client):
    resp = client.post("/api/v1/copilot/ask", json={"question": "Who is PR001?", "rm_id": "RM01"})
    assert resp.status_code == 200
    body = resp.json()
    assert "answer" in body
    assert "provider" in body
    assert body["provider"] in ("rule_based", "claude/claude-haiku-4-5-20251001", "gemini/gemini-1.5-flash")
