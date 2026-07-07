"""Lead scoring weights and NBA configuration.

Rule-based scorecard — fully deterministic and explainable.
Identical feature vectors always produce byte-identical scores.
"""
from __future__ import annotations

SCORE_VERSION = "2026.07.1"

# Weights sum to 100
WEIGHTS: dict[str, float] = {
    "credit_bureau":       25.0,
    "income":              20.0,
    "digital_activity":    15.0,
    "life_event":          15.0,
    "recency":             10.0,
    "existing_customer":   10.0,
    "enquiry_penalty":      5.0,  # negative weight
}

LIFE_EVENT_BOOST: dict[str, float] = {
    "home_purchase":       10.0,
    "vehicle_purchase":     8.0,
    "marriage":             9.0,
    "child_education":      7.0,
    "business_expansion":   9.0,
    "retirement_planning":  8.0,
    "first_job":            6.0,
    "wealth_transfer":      7.0,
}

BAND_THRESHOLDS = [
    (80, "Hot"),
    (60, "Warm"),
    (40, "Lukewarm"),
    (0,  "Cold"),
]

# Product recommendation matrix: segment × life_event → product
NBA_PRODUCT: dict[str, dict[str, str]] = {
    "Salaried": {
        "home_purchase":    "Home Loan",
        "vehicle_purchase": "Auto Loan",
        "marriage":         "Personal Loan",
        "child_education":  "Education Loan",
        "first_job":        "Salary Account + Credit Card",
        "default":          "Personal Loan",
    },
    "Self-Employed": {
        "business_expansion": "Business Loan / OD",
        "vehicle_purchase":   "Auto Loan",
        "home_purchase":      "Mortgage Loan",
        "default":            "Current Account + CC Limit",
    },
    "HNI": {
        "retirement_planning": "Wealth Management / PMS",
        "wealth_transfer":     "Estate Planning + NRI Products",
        "business_expansion":  "Corporate Banking",
        "default":             "Priority Banking",
    },
}

NBA_CHANNEL: dict[str, str] = {
    "Hot":      "Direct RM call today",
    "Warm":     "WhatsApp + follow-up call",
    "Lukewarm": "Email nurture sequence",
    "Cold":     "Monthly newsletter only",
}

NBA_TIMING: dict[str, str] = {
    "Hot":      "Within 24 hours",
    "Warm":     "Within 3 days",
    "Lukewarm": "Within 2 weeks",
    "Cold":     "Next quarter",
}
