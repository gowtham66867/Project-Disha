"""Fairness regression tests.

Identical financial profiles must produce identical lead scores regardless
of the prospect's name, gender signal in name, city, or state.
IDBI Fair Lending + RBI ML model governance require this.
"""
from __future__ import annotations

import pytest
from app.scoring.scorer import compute_lead_score

FINANCIAL_BASE = {
    "prospect_id": "F001",
    "segment": "Salaried",
    "annual_income": 1500000,
    "existing_customer": False,
    "digital_activity_score": 72,
    "last_interaction_days": 7,
    "life_event": "home_purchase",
    "credit_bureau_score": 730,
    "loan_enquiries_6m": 1,
}


def test_score_unaffected_by_name():
    r1 = compute_lead_score({**FINANCIAL_BASE, "prospect_id": "F001", "name": "Rajesh Kumar"})
    r2 = compute_lead_score({**FINANCIAL_BASE, "prospect_id": "F002", "name": "Fatima Shaikh"})
    assert r1.lead_score == r2.lead_score, "Name must not influence score"


def test_score_unaffected_by_city():
    r1 = compute_lead_score({**FINANCIAL_BASE, "city": "Mumbai", "state": "Maharashtra"})
    r2 = compute_lead_score({**FINANCIAL_BASE, "city": "Patna", "state": "Bihar"})
    assert r1.lead_score == r2.lead_score, "Geography must not influence score"


def test_score_unaffected_by_employer_category():
    r1 = compute_lead_score({**FINANCIAL_BASE, "employer_category": "MNC"})
    r2 = compute_lead_score({**FINANCIAL_BASE, "employer_category": "Government"})
    r3 = compute_lead_score({**FINANCIAL_BASE, "employer_category": "Startup"})
    assert r1.lead_score == r2.lead_score == r3.lead_score, \
        "Employer category must not influence score"


def test_score_unaffected_by_rm_assignment():
    r1 = compute_lead_score({**FINANCIAL_BASE, "rm_id": "RM01"})
    r2 = compute_lead_score({**FINANCIAL_BASE, "rm_id": "RM99"})
    assert r1.lead_score == r2.lead_score, "RM assignment must not influence score"
