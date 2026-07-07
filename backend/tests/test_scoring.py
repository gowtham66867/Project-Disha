"""Unit tests for the deterministic lead scoring engine."""
from __future__ import annotations

import pytest
from app.scoring.scorer import compute_lead_score


BASE = {
    "prospect_id": "TEST001",
    "segment": "Salaried",
    "annual_income": 1200000,
    "existing_customer": False,
    "digital_activity_score": 70,
    "last_interaction_days": 5,
    "life_event": "home_purchase",
    "credit_bureau_score": 740,
    "loan_enquiries_6m": 1,
}


def test_score_is_deterministic():
    r1 = compute_lead_score(BASE)
    r2 = compute_lead_score(BASE)
    assert r1.lead_score == r2.lead_score
    assert r1.lead_band == r2.lead_band


def test_score_in_range():
    r = compute_lead_score(BASE)
    assert 0 <= r.lead_score <= 100


def test_hot_band_for_strong_prospect():
    p = {**BASE, "credit_bureau_score": 800, "annual_income": 5000000,
         "digital_activity_score": 95, "existing_customer": True, "loan_enquiries_6m": 0}
    r = compute_lead_score(p)
    assert r.lead_band in ("Hot", "Warm")
    assert r.lead_score >= 60


def test_cold_band_for_weak_prospect():
    p = {**BASE, "credit_bureau_score": 610, "annual_income": 300000,
         "digital_activity_score": 10, "loan_enquiries_6m": 4, "life_event": None,
         "last_interaction_days": 60}
    r = compute_lead_score(p)
    assert r.lead_score < 60


def test_contributions_sum_to_score():
    r = compute_lead_score(BASE)
    total = sum(c.contribution for c in r.contributions)
    assert abs(total - r.lead_score) < 0.1


def test_nba_product_assigned():
    r = compute_lead_score(BASE)
    assert r.recommended_product != ""
    assert r.recommended_channel != ""
    assert r.recommended_timing != ""


def test_existing_customer_boosts_score():
    base_score = compute_lead_score({**BASE, "existing_customer": False}).lead_score
    existing_score = compute_lead_score({**BASE, "existing_customer": True}).lead_score
    assert existing_score > base_score


def test_high_enquiries_penalises_score():
    low = compute_lead_score({**BASE, "loan_enquiries_6m": 0}).lead_score
    high = compute_lead_score({**BASE, "loan_enquiries_6m": 4}).lead_score
    assert high < low
