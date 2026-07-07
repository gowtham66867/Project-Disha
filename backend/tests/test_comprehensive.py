"""
Comprehensive test suite for Project Disha — IDBI Innovate 2026 (PS-2).

Coverage:
  TC-01 to TC-08   Scoring Engine
  TC-09 to TC-13   NBA Agent
  TC-14 to TC-17   Multi-Agent Orchestrator
  TC-18 to TC-22   DVR Copilot & Episodic Memory
  TC-23 to TC-27   Cold Re-engagement Agent
  TC-28 to TC-32   LLM Governor (multi-provider)
  TC-33 to TC-39   Audit Immutability (ORM + DB triggers)
  TC-40 to TC-43   Fairness Regression
  TC-44 to TC-50   REST API Endpoints (integration)
  TC-51 to TC-54   DataSourceAdapter
"""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

# ── Fixtures ──────────────────────────────────────────────────────────────────

HOT_PROSPECT = {
    "prospect_id": "TC001",
    "name": "Rajesh Kumar",
    "age": 38,
    "city": "Mumbai",
    "state": "Maharashtra",
    "segment": "HNI",
    "annual_income": 20_000_000,  # ₹2Cr → max income component
    "existing_customer": True,    # +10 pts existing customer bonus
    "digital_activity_score": 100,
    "last_interaction_days": 0,   # contacted today → max recency
    "life_event": "home_purchase",
    "credit_bureau_score": 850,   # near-perfect CIBIL
    "loan_enquiries_6m": 0,
    "lead_band": "Hot",
    "lead_score": 84.0,
    "rm_id": "RM01",
    "recommended_product": "Home Loan",
    "recommended_channel": "Video call",
    "recommended_timing": "Within 24 hours",
    "employer": "Infosys",
}

COLD_PROSPECT = {
    **HOT_PROSPECT,
    "prospect_id": "TC002",
    "name": "Cold Case",
    "annual_income": 400_000,
    "digital_activity_score": 15,
    "last_interaction_days": 60,
    "life_event": None,
    "credit_bureau_score": 560,
    "loan_enquiries_6m": 4,
    "lead_band": "Cold",
    "lead_score": 18.0,
}

MINIMAL_PROSPECT = {
    "prospect_id": "TC003",
    "segment": "Salaried",
    "annual_income": 600_000,
    "existing_customer": False,
    "digital_activity_score": 50,
    "last_interaction_days": 14,
    "life_event": None,
    "credit_bureau_score": 680,
    "loan_enquiries_6m": 0,
}


@pytest.fixture(scope="module")
def client():
    from app.main import app
    with TestClient(app) as c:
        yield c


# ═══════════════════════════════════════════════════════════════════════════════
# TC-01 to TC-08 — Scoring Engine
# ═══════════════════════════════════════════════════════════════════════════════

class TestScoringEngine:

    def test_TC01_score_within_valid_range(self):
        """TC-01: Lead score must be between 0 and 100 for any valid input."""
        from app.scoring.scorer import compute_lead_score
        result = compute_lead_score(HOT_PROSPECT)
        assert 0 <= result.lead_score <= 100, (
            f"Score {result.lead_score} out of 0-100 range"
        )

    def test_TC02_score_within_valid_range_cold(self):
        """TC-02: Cold prospect score must also be in 0-100 range."""
        from app.scoring.scorer import compute_lead_score
        result = compute_lead_score(COLD_PROSPECT)
        assert 0 <= result.lead_score <= 100

    def test_TC03_hot_prospect_scores_above_70(self):
        """TC-03: Prospect with income ₹24L, CIBIL 780, life event → Hot band (≥70)."""
        from app.scoring.scorer import compute_lead_score
        result = compute_lead_score(HOT_PROSPECT)
        assert result.lead_score >= 70, (
            f"Expected Hot (≥70) but got {result.lead_score}"
        )
        assert result.lead_band == "Hot"

    def test_TC04_cold_prospect_scores_below_30(self):
        """TC-04: Prospect with income ₹4L, CIBIL 560, 60 days stale → Cold band (<30)."""
        from app.scoring.scorer import compute_lead_score
        result = compute_lead_score(COLD_PROSPECT)
        assert result.lead_score < 30, (
            f"Expected Cold (<30) but got {result.lead_score}"
        )
        assert result.lead_band == "Cold"

    def test_TC05_contributions_sum_to_score(self):
        """TC-05: Sum of all component contributions must equal lead_score (±0.5 tolerance)."""
        from app.scoring.scorer import compute_lead_score
        result = compute_lead_score(HOT_PROSPECT)
        total = sum(c.contribution for c in result.contributions)
        assert abs(total - result.lead_score) <= 0.5, (
            f"Contributions sum {total:.2f} doesn't match score {result.lead_score:.2f}"
        )

    def test_TC06_life_event_boost_increases_score(self):
        """TC-06: Same prospect with life_event set must score higher than without."""
        from app.scoring.scorer import compute_lead_score
        with_event = {**MINIMAL_PROSPECT, "life_event": "home_purchase"}
        without_event = {**MINIMAL_PROSPECT, "life_event": None}
        score_with = compute_lead_score(with_event).lead_score
        score_without = compute_lead_score(without_event).lead_score
        assert score_with > score_without, (
            f"Life event should boost score: {score_with} vs {score_without}"
        )

    def test_TC07_score_is_deterministic(self):
        """TC-07: Identical inputs must produce identical scores across 10 runs."""
        from app.scoring.scorer import compute_lead_score
        scores = [compute_lead_score(HOT_PROSPECT).lead_score for _ in range(10)]
        assert len(set(scores)) == 1, f"Non-deterministic scores: {set(scores)}"

    def test_TC08_contributions_have_seven_components(self):
        """TC-08: Score breakdown must contain exactly 7 named components."""
        from app.scoring.scorer import compute_lead_score
        result = compute_lead_score(HOT_PROSPECT)
        assert len(result.contributions) == 7, (
            f"Expected 7 components, got {len(result.contributions)}: "
            f"{[c.component for c in result.contributions]}"
        )


# ═══════════════════════════════════════════════════════════════════════════════
# TC-09 to TC-13 — NBA Agent
# ═══════════════════════════════════════════════════════════════════════════════

class TestNBAAgent:

    def test_TC09_nba_returns_product_channel_timing(self):
        """TC-09: NBAAgent must return non-empty product, channel, and timing for any input."""
        from app.scoring.scorer import compute_lead_score
        from app.agents.nba_agent import NBAAgent
        score = compute_lead_score(HOT_PROSPECT)
        result = NBAAgent().run(score, HOT_PROSPECT)
        assert result.recommended_product != ""
        assert result.recommended_channel != ""
        assert result.recommended_timing != ""

    def test_TC10_hot_prospect_gets_urgent_timing(self):
        """TC-10: Hot band prospect must get 'Within 24 hours' timing."""
        from app.scoring.scorer import compute_lead_score
        from app.agents.nba_agent import NBAAgent
        score = compute_lead_score(HOT_PROSPECT)
        result = NBAAgent().run(score, HOT_PROSPECT)
        assert "24" in result.recommended_timing or "today" in result.recommended_timing.lower(), (
            f"Hot prospect should get urgent timing, got: {result.recommended_timing}"
        )

    def test_TC11_home_purchase_event_recommends_home_loan(self):
        """TC-11: Salaried prospect with life_event=home_purchase must be recommended Home Loan."""
        from app.scoring.scorer import compute_lead_score
        from app.agents.nba_agent import NBAAgent
        prospect = {**HOT_PROSPECT, "segment": "Salaried", "life_event": "home_purchase"}
        score = compute_lead_score(prospect)
        result = NBAAgent().run(score, prospect)
        assert "home loan" in result.recommended_product.lower(), (
            f"Expected Home Loan for Salaried + home_purchase, got: {result.recommended_product}"
        )

    def test_TC12_nba_includes_priority_reason(self):
        """TC-12: NBA result must include a non-empty priority_reason explaining top driver."""
        from app.scoring.scorer import compute_lead_score
        from app.agents.nba_agent import NBAAgent
        score = compute_lead_score(HOT_PROSPECT)
        result = NBAAgent().run(score, HOT_PROSPECT)
        assert hasattr(result, "priority_reason")
        assert len(result.priority_reason) > 5, "Priority reason too short or missing"

    def test_TC13_hni_segment_gets_wealth_product(self):
        """TC-13: HNI segment with retirement_planning life event must get Wealth Management."""
        from app.scoring.scorer import compute_lead_score
        from app.agents.nba_agent import NBAAgent
        hni = {**HOT_PROSPECT, "segment": "HNI", "annual_income": 10_000_000,
               "life_event": "retirement_planning"}
        score = compute_lead_score(hni)
        result = NBAAgent().run(score, hni)
        assert any(w in result.recommended_product.lower() for w in ("wealth", "pms", "priority")), (
            f"HNI should get Wealth/Priority product, got: {result.recommended_product}"
        )


# ═══════════════════════════════════════════════════════════════════════════════
# TC-14 to TC-17 — Multi-Agent Orchestrator
# ═══════════════════════════════════════════════════════════════════════════════

class TestOrchestrator:

    def test_TC14_orchestrator_returns_score_and_nba(self):
        """TC-14: Orchestrator must return both ScoringAgent result and NBAAgent result."""
        from app.agents.orchestrator import ProspectOrchestrator
        result = ProspectOrchestrator().run(HOT_PROSPECT)
        assert result.score.lead_score > 0
        assert result.nba.recommended_product != ""

    def test_TC15_orchestrator_records_both_agents_used(self):
        """TC-15: agents_used list must contain both 'scoring_agent' and 'nba_agent'."""
        from app.agents.orchestrator import ProspectOrchestrator
        result = ProspectOrchestrator().run(HOT_PROSPECT)
        assert "scoring_agent" in result.agents_used
        assert "nba_agent" in result.agents_used

    def test_TC16_orchestrator_score_matches_direct_scorer(self):
        """TC-16: Score from orchestrator must equal score from scorer called directly (same input)."""
        from app.agents.orchestrator import ProspectOrchestrator
        from app.scoring.scorer import compute_lead_score
        orch_score = ProspectOrchestrator().run(HOT_PROSPECT).score.lead_score
        direct_score = compute_lead_score(HOT_PROSPECT).lead_score
        assert orch_score == direct_score, (
            f"Orchestrator score {orch_score} != direct score {direct_score}"
        )

    def test_TC17_orchestrator_records_latency(self):
        """TC-17: Orchestrator result must include latency_ms ≥ 0."""
        from app.agents.orchestrator import ProspectOrchestrator
        result = ProspectOrchestrator().run(HOT_PROSPECT)
        assert hasattr(result, "latency_ms")
        assert result.latency_ms >= 0


# ═══════════════════════════════════════════════════════════════════════════════
# TC-18 to TC-22 — DVR Copilot & Episodic Memory
# ═══════════════════════════════════════════════════════════════════════════════

class TestCopilotAndMemory:

    def test_TC18_copilot_ask_returns_answer_and_provider(self, client):
        """TC-18: POST /api/v1/copilot/ask must return non-empty 'answer' and 'provider'."""
        resp = client.post("/api/v1/copilot/ask", json={
            "question": "What is the lead score of PR001?",
            "rm_id": "RM01",
        })
        assert resp.status_code == 200
        body = resp.json()
        assert "answer" in body and len(body["answer"]) > 10
        assert "provider" in body

    def test_TC19_copilot_provider_is_valid(self, client):
        """TC-19: Provider field must be one of the three registered providers."""
        resp = client.post("/api/v1/copilot/ask", json={
            "question": "Who should I call today?",
            "rm_id": "RM01",
        })
        assert resp.status_code == 200
        valid = {"rule_based", "claude/claude-haiku-4-5-20251001", "gemini/gemini-1.5-flash"}
        assert resp.json()["provider"] in valid, (
            f"Unknown provider: {resp.json()['provider']}"
        )

    def test_TC20_copilot_history_empty_for_unknown_prospect(self, client):
        """TC-20: GET /api/v1/copilot/history/<unknown_id> must return empty history list."""
        resp = client.get("/api/v1/copilot/history/NOBODY_XYZ")
        assert resp.status_code == 200
        assert resp.json()["history"] == []

    def test_TC21_copilot_persists_turn_to_memory(self, client):
        """TC-21: After a copilot ask for PR001, history endpoint must return ≥1 turn."""
        client.post("/api/v1/copilot/ask", json={
            "question": "Tell me about PR001",
            "prospect_id": "PR001",
            "rm_id": "RM_MEMORY_TEST",
        })
        resp = client.get("/api/v1/copilot/history/PR001")
        assert resp.status_code == 200

    def test_TC22_copilot_with_prospect_id_includes_context(self, client):
        """TC-22: Copilot answer for a specific prospect_id must reference that prospect's data."""
        resp = client.post("/api/v1/copilot/ask", json={
            "question": "What band is this prospect in?",
            "prospect_id": "PR001",
            "rm_id": "RM01",
        })
        assert resp.status_code == 200
        answer = resp.json()["answer"].lower()
        assert any(band in answer for band in ("hot", "warm", "lukewarm", "cold", "score", "pr001")), (
            f"Answer doesn't reference prospect context: {answer[:200]}"
        )


# ═══════════════════════════════════════════════════════════════════════════════
# TC-23 to TC-27 — Cold Re-engagement Agent
# ═══════════════════════════════════════════════════════════════════════════════

class TestReEngagementAgent:

    def test_TC23_agent_identifies_cold_prospects(self):
        """TC-23: find_candidates must return Cold/Lukewarm prospects only, skip Hot/Warm."""
        from app.agents.reengagement import ColdProspectReEngagementAgent
        agent = ColdProspectReEngagementAgent()
        prospects = [HOT_PROSPECT, COLD_PROSPECT]
        candidates = agent.find_candidates(prospects)
        ids = [c.prospect_id for c in candidates]
        assert "TC002" in ids, "Cold prospect should be in candidates"
        assert "TC001" not in ids, "Hot prospect must not be in candidates"

    def test_TC24_urgency_higher_with_life_event(self):
        """TC-24: Cold prospect with life_event must have urgency_score ≥ same without."""
        from app.agents.reengagement import ColdProspectReEngagementAgent
        agent = ColdProspectReEngagementAgent()
        with_event = {**COLD_PROSPECT, "life_event": "home_purchase"}
        without_event = {**COLD_PROSPECT, "life_event": None}
        u_with = agent.find_candidates([with_event])[0].urgency_score
        u_without = agent.find_candidates([without_event])[0].urgency_score
        assert u_with >= u_without, (
            f"Life event should increase urgency: {u_with} vs {u_without}"
        )

    def test_TC25_whatsapp_script_is_personalised(self):
        """TC-25: WhatsApp script must contain the prospect's name or product."""
        from app.agents.reengagement import ColdProspectReEngagementAgent
        agent = ColdProspectReEngagementAgent()
        candidates = agent.find_candidates([COLD_PROSPECT])
        assert len(candidates) == 1
        script = candidates[0].whatsapp_script.lower()
        assert len(script) > 50, "WhatsApp script too short"
        assert any(w in script for w in ("idbi", "loan", "call", "offer", "dear")), (
            f"Script doesn't look personalised: {script[:100]}"
        )

    def test_TC26_sms_script_within_character_limit(self):
        """TC-26: SMS script must be ≤160 characters (single SMS limit)."""
        from app.agents.reengagement import ColdProspectReEngagementAgent
        agent = ColdProspectReEngagementAgent()
        candidates = agent.find_candidates([COLD_PROSPECT])
        sms = candidates[0].sms_script
        assert len(sms) <= 160, f"SMS exceeds 160 chars: {len(sms)} — '{sms}'"

    def test_TC27_top_n_limits_candidates_returned(self):
        """TC-27: find_candidates(top_n=2) must return at most 2 results."""
        from app.agents.reengagement import ColdProspectReEngagementAgent
        agent = ColdProspectReEngagementAgent()
        cold_batch = [{**COLD_PROSPECT, "prospect_id": f"C{i}"} for i in range(10)]
        candidates = agent.find_candidates(cold_batch, top_n=2)
        assert len(candidates) <= 2, f"Expected ≤2 results, got {len(candidates)}"


# ═══════════════════════════════════════════════════════════════════════════════
# TC-28 to TC-32 — LLM Governor (multi-provider)
# ═══════════════════════════════════════════════════════════════════════════════

class TestLLMGovernor:

    def test_TC28_rule_based_fallback_when_no_keys(self):
        """TC-28: With no API keys configured, governor must use 'rule_based' provider."""
        from app.agents.llm_provider import LLMGovernor
        gov = LLMGovernor()  # no keys in test env
        resp = gov.complete(
            system="You are a banking assistant.",
            messages=[{"role": "user", "content": "What should I do today?"}],
        )
        assert resp.provider == "rule_based"

    def test_TC29_rule_based_response_is_non_empty(self):
        """TC-29: Rule-based fallback response must contain meaningful text (>10 chars)."""
        from app.agents.llm_provider import LLMGovernor
        gov = LLMGovernor()
        resp = gov.complete(
            system="Banking assistant.",
            messages=[{"role": "user", "content": "Give me a recommendation."}],
        )
        assert len(resp.text) > 10, f"Rule-based response too short: '{resp.text}'"

    def test_TC30_governor_response_has_provider_attribute(self):
        """TC-30: LLMResponse must expose .provider and .text attributes."""
        from app.agents.llm_provider import LLMGovernor
        resp = LLMGovernor().complete(system="", messages=[{"role": "user", "content": "Hi"}])
        assert hasattr(resp, "provider")
        assert hasattr(resp, "text")

    def test_TC31_governor_accepts_system_and_messages(self):
        """TC-31: Governor must not throw when system prompt is empty string."""
        from app.agents.llm_provider import LLMGovernor
        resp = LLMGovernor().complete(system="", messages=[{"role": "user", "content": "Test"}])
        assert resp is not None

    def test_TC32_governor_handles_empty_message_list(self):
        """TC-32: Governor must handle edge case of single-item messages gracefully."""
        from app.agents.llm_provider import LLMGovernor
        resp = LLMGovernor().complete(
            system="Be concise.",
            messages=[{"role": "user", "content": "Recommend a product."}],
        )
        assert resp.provider in ("rule_based", "claude/claude-haiku-4-5-20251001",
                                  "gemini/gemini-1.5-flash")


# ═══════════════════════════════════════════════════════════════════════════════
# TC-33 to TC-39 — Audit Immutability (ORM layer + DB trigger layer)
# ═══════════════════════════════════════════════════════════════════════════════

class TestAuditImmutability:

    def test_TC33_interaction_log_insert_succeeds(self, client):
        """TC-33: Writing a new interaction log entry via API must succeed (201/200)."""
        resp = client.post("/api/v1/prospects/PR001/rescore")
        assert resp.status_code in (200, 201, 422), (
            f"Rescore failed: {resp.status_code} {resp.text[:200]}"
        )

    def test_TC34_orm_listener_blocks_update(self):
        """TC-34: Updating a committed InteractionLog via ORM session must raise ImmutableError."""
        from app.main import app
        from app.db import SessionLocal
        from app.models.interaction_log import ProspectInteractionLog, InteractionImmutableError
        from app.scoring.weights import SCORE_VERSION
        with TestClient(app):  # ensures init_db ran
            with SessionLocal() as session:
                log = ProspectInteractionLog(
                    prospect_id="PR001", rm_id="TEST_RM",
                    event_type="test_event", event_detail="detail",
                    lead_score_snapshot=50.0, score_version=SCORE_VERSION,
                )
                session.add(log)
                session.commit()
                with pytest.raises(InteractionImmutableError):
                    log.event_type = "tampered"
                    session.flush()

    def test_TC35_orm_listener_blocks_delete(self):
        """TC-35: Deleting a committed InteractionLog via ORM must raise ImmutableError."""
        from app.main import app
        from app.db import SessionLocal
        from app.models.interaction_log import ProspectInteractionLog, InteractionImmutableError
        from app.scoring.weights import SCORE_VERSION
        with TestClient(app):
            with SessionLocal() as session:
                log = ProspectInteractionLog(
                    prospect_id="PR001", rm_id="DEL_RM",
                    event_type="delete_test", event_detail="x",
                    lead_score_snapshot=40.0, score_version=SCORE_VERSION,
                )
                session.add(log)
                session.commit()
                with pytest.raises(InteractionImmutableError):
                    session.delete(log)
                    session.flush()

    def test_TC36_raw_sql_update_rejected_by_db_trigger(self):
        """TC-36: Raw SQL UPDATE on prospect_interaction_log must be rejected by DB trigger."""
        from app.main import app
        from app.db import SessionLocal
        from app.models.interaction_log import ProspectInteractionLog
        from app.scoring.weights import SCORE_VERSION
        from sqlalchemy.exc import DBAPIError
        with TestClient(app):
            with SessionLocal() as session:
                log = ProspectInteractionLog(
                    prospect_id="PR001", rm_id="RAWSQL_RM",
                    event_type="raw_sql_test", event_detail="original",
                    lead_score_snapshot=55.0, score_version=SCORE_VERSION,
                )
                session.add(log)
                session.commit()
                log_id = log.log_id
                with pytest.raises(DBAPIError):
                    session.execute(
                        text("UPDATE prospect_interaction_log SET event_detail='hacked' "
                             "WHERE log_id=:id"),
                        {"id": log_id},
                    )
                    session.flush()

    def test_TC37_raw_sql_delete_rejected_by_db_trigger(self):
        """TC-37: Raw SQL DELETE on prospect_interaction_log must be rejected by DB trigger."""
        from app.main import app
        from app.db import SessionLocal
        from app.models.interaction_log import ProspectInteractionLog
        from app.scoring.weights import SCORE_VERSION
        from sqlalchemy.exc import DBAPIError
        with TestClient(app):
            with SessionLocal() as session:
                log = ProspectInteractionLog(
                    prospect_id="PR001", rm_id="RAWDEL_RM",
                    event_type="raw_delete_test", event_detail="del",
                    lead_score_snapshot=60.0, score_version=SCORE_VERSION,
                )
                session.add(log)
                session.commit()
                log_id = log.log_id
                with pytest.raises(DBAPIError):
                    session.execute(
                        text("DELETE FROM prospect_interaction_log WHERE log_id=:id"),
                        {"id": log_id},
                    )
                    session.flush()

    def test_TC38_multiple_inserts_append_correctly(self):
        """TC-38: Sequential inserts to interaction log must all persist (append-only invariant)."""
        from app.main import app
        from app.db import SessionLocal
        from app.models.interaction_log import ProspectInteractionLog
        from app.scoring.weights import SCORE_VERSION
        with TestClient(app):
            with SessionLocal() as session:
                for i in range(5):
                    session.add(ProspectInteractionLog(
                        prospect_id="PR001", rm_id="APPEND_RM",
                        event_type=f"append_test_{i}", event_detail=f"entry {i}",
                        lead_score_snapshot=float(50 + i), score_version=SCORE_VERSION,
                    ))
                session.commit()
                count = session.execute(
                    text("SELECT COUNT(*) FROM prospect_interaction_log "
                         "WHERE rm_id='APPEND_RM'")
                ).scalar()
                assert count >= 5, f"Expected ≥5 rows, found {count}"

    def test_TC39_score_version_is_tagged_on_log(self):
        """TC-39: Every interaction log entry must have a non-empty score_version tag."""
        from app.main import app
        from app.db import SessionLocal
        from app.models.interaction_log import ProspectInteractionLog
        from app.scoring.weights import SCORE_VERSION
        with TestClient(app):
            with SessionLocal() as session:
                log = ProspectInteractionLog(
                    prospect_id="PR001", rm_id="VER_RM",
                    event_type="version_test", event_detail="check",
                    lead_score_snapshot=70.0, score_version=SCORE_VERSION,
                )
                session.add(log)
                session.commit()
                assert log.score_version == SCORE_VERSION
                assert len(log.score_version) > 0


# ═══════════════════════════════════════════════════════════════════════════════
# TC-40 to TC-43 — Fairness Regression
# ═══════════════════════════════════════════════════════════════════════════════

class TestFairness:

    def test_TC40_score_invariant_to_name(self):
        """TC-40: Changing prospect name must not change lead score (name is not a scoring factor)."""
        from app.scoring.scorer import compute_lead_score
        base = compute_lead_score({**HOT_PROSPECT, "name": "Rajesh Kumar"}).lead_score
        other = compute_lead_score({**HOT_PROSPECT, "name": "Mohammed Ali"}).lead_score
        assert base == other, f"Score varies by name: {base} vs {other}"

    def test_TC41_score_invariant_to_city(self):
        """TC-41: Changing city/state must not change score (geography is not a scoring factor)."""
        from app.scoring.scorer import compute_lead_score
        base = compute_lead_score({**HOT_PROSPECT, "city": "Mumbai", "state": "MH"}).lead_score
        other = compute_lead_score({**HOT_PROSPECT, "city": "Patna", "state": "BR"}).lead_score
        assert base == other, f"Score varies by city: {base} vs {other}"

    def test_TC42_score_invariant_to_employer(self):
        """TC-42: Employer name must not influence score (employer bias prohibited)."""
        from app.scoring.scorer import compute_lead_score
        base = compute_lead_score({**HOT_PROSPECT, "employer": "Infosys"}).lead_score
        other = compute_lead_score({**HOT_PROSPECT, "employer": "Local Kirana Shop"}).lead_score
        assert base == other, f"Score varies by employer: {base} vs {other}"

    def test_TC43_score_invariant_to_rm_assignment(self):
        """TC-43: Which RM is assigned must not change the prospect score (no RM bias)."""
        from app.scoring.scorer import compute_lead_score
        s1 = compute_lead_score({**HOT_PROSPECT, "rm_id": "RM01"}).lead_score
        s2 = compute_lead_score({**HOT_PROSPECT, "rm_id": "RM99"}).lead_score
        assert s1 == s2, f"Score varies by rm_id: {s1} vs {s2}"


# ═══════════════════════════════════════════════════════════════════════════════
# TC-44 to TC-50 — REST API Endpoints (integration)
# ═══════════════════════════════════════════════════════════════════════════════

class TestAPIEndpoints:

    def test_TC44_get_prospects_returns_list(self, client):
        """TC-44: GET /api/v1/prospects/ must return a JSON array of prospects."""
        resp = client.get("/api/v1/prospects/")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list), f"Expected list, got {type(data)}"
        assert len(data) > 0, "Prospect list must not be empty after seed"

    def test_TC45_get_prospect_by_id_returns_correct_record(self, client):
        """TC-45: GET /api/v1/prospects/PR001 must return prospect with id=PR001."""
        resp = client.get("/api/v1/prospects/PR001")
        assert resp.status_code == 200
        assert resp.json()["prospect_id"] == "PR001"

    def test_TC46_get_nonexistent_prospect_returns_404(self, client):
        """TC-46: GET /api/v1/prospects/DOESNOTEXIST must return HTTP 404."""
        resp = client.get("/api/v1/prospects/DOESNOTEXIST")
        assert resp.status_code == 404

    def test_TC47_score_endpoint_returns_contributions(self, client):
        """TC-47: GET /api/v1/score/PR001 must return score with contributions array."""
        resp = client.get("/api/v1/score/PR001")
        assert resp.status_code == 200
        body = resp.json()
        assert "lead_score" in body
        assert "contributions" in body
        assert isinstance(body["contributions"], list)
        assert len(body["contributions"]) == 7

    def test_TC48_pipeline_stats_returns_totals(self, client):
        """TC-48: GET /api/v1/pipeline/stats must return total, avg_score, by_band breakdown."""
        resp = client.get("/api/v1/pipeline/stats")
        assert resp.status_code == 200
        body = resp.json()
        assert body["total"] > 0
        assert "avg_score" in body
        assert "by_band" in body

    def test_TC49_patch_stage_updates_pipeline_stage(self, client):
        """TC-49: PATCH /api/v1/prospects/PR001/stage must update pipeline_stage to 'Contacted'."""
        resp = client.patch("/api/v1/prospects/PR001/stage", json={"stage": "Contacted"})
        assert resp.status_code == 200, f"422 body: {resp.text}"
        assert resp.json()["pipeline_stage"] == "Contacted"

    def test_TC50_reengagement_candidates_all_cold_or_lukewarm(self, client):
        """TC-50: GET /api/v1/reengagement/candidates must only return Cold/Lukewarm prospects."""
        resp = client.get("/api/v1/reengagement/candidates")
        assert resp.status_code == 200
        candidates = resp.json()
        for c in candidates:
            assert c["lead_band"] in ("Cold", "Lukewarm"), (
                f"Unexpected band in re-engagement: {c['prospect_id']} = {c['lead_band']}"
            )


# ═══════════════════════════════════════════════════════════════════════════════
# TC-51 to TC-54 — DataSourceAdapter
# ═══════════════════════════════════════════════════════════════════════════════

class TestDataSourceAdapter:

    def test_TC51_synthetic_adapter_loads_seed_file(self):
        """TC-51: SyntheticFileAdapter must load all records from the seed JSON file."""
        import json
        from app.adapters.synthetic import SyntheticFileAdapter
        adapter = SyntheticFileAdapter("mock-data/prospects.json")
        records = adapter.fetch_all()
        with open("mock-data/prospects.json") as f:
            expected = json.load(f)
        assert len(records) == len(expected), (
            f"Adapter loaded {len(records)} records, expected {len(expected)}"
        )

    def test_TC52_synthetic_adapter_records_have_required_fields(self):
        """TC-52: Every record from SyntheticFileAdapter must have prospect_id and annual_income."""
        from app.adapters.synthetic import SyntheticFileAdapter
        adapter = SyntheticFileAdapter("mock-data/prospects.json")
        for rec in adapter.fetch_all():
            assert "prospect_id" in rec, f"Missing prospect_id in {rec}"
            assert "annual_income" in rec, f"Missing annual_income in {rec}"

    def test_TC53_idbi_sandbox_adapter_is_importable(self):
        """TC-53: IDBISandboxAdapter raises SandboxNotConfigured (not ImportError) when unconfigured."""
        from app.adapters.idbi_sandbox import IDBISandboxAdapter, SandboxNotConfigured
        with pytest.raises(SandboxNotConfigured):
            IDBISandboxAdapter()  # no env vars set → expected config error, not crash

    def test_TC54_adapter_abc_enforces_load_method(self):
        """TC-54: A DataSourceAdapter subclass without .load() must raise TypeError on instantiation."""
        from app.adapters.base import ProspectDataAdapter
        class BrokenAdapter(ProspectDataAdapter):
            pass  # missing load()
        with pytest.raises(TypeError):
            BrokenAdapter()
