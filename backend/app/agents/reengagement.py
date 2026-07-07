"""ColdProspectReEngagementAgent — mirrors CineAgent's RetentionAgent.

Finds Lukewarm/Cold prospects, scores their re-engagement potential,
and generates a personalised WhatsApp/SMS nudge script.  Optional CPaaS
send via CPAAS_WEBHOOK_URL (mock-friendly — logs instead if not set).

Pattern:
    scan cold prospects → score re-engagement opportunity
    → generate vernacular WhatsApp script → (optionally) send via CPaaS
"""
from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass, field
from typing import Optional

log = logging.getLogger(__name__)

COLD_BANDS = {"Cold", "Lukewarm"}

# Re-engagement urgency: life event + days since contact
_URGENCY_RULES = [
    (lambda p: p.get("life_event") in ("home_purchase", "marriage", "business_expansion"), 15),
    (lambda p: p.get("existing_customer"), 10),
    (lambda p: p.get("last_interaction_days", 99) > 30, 5),
]


@dataclass
class ReEngagementCandidate:
    prospect_id: str
    name: str
    segment: str
    lead_band: str
    lead_score: float
    life_event: str
    recommended_product: str
    days_since_contact: int
    urgency_score: int
    whatsapp_script: str
    sms_script: str


def _urgency(p: dict) -> int:
    return sum(pts for rule, pts in _URGENCY_RULES if rule(p))


def _whatsapp_script(p: dict) -> str:
    name = p.get("name", "Sir/Madam").split()[0]
    product = p.get("recommended_product", "our banking products")
    event = (p.get("life_event") or "").replace("_", " ")
    event_line = f" We noticed you may be planning a {event}." if event else ""
    return (
        f"🙏 Namaste {name}!{event_line}\n\n"
        f"IDBI Bank has a special offer on {product} tailored for you. "
        f"Your pre-approval is ready — no documents needed for the first step.\n\n"
        f"Reply *YES* to know more or call your RM directly. "
        f"Offer valid for 7 days.\n\n"
        f"*IDBI Bank — Aapka Apna Bank* 🏦"
    )


def _sms_script(p: dict) -> str:
    name = p.get("name", "Customer").split()[0]
    product = p.get("recommended_product", "our products")
    return f"Dear {name}, IDBI Bank: Special {product} offer for you. Pre-approved. Reply YES or call RM. -IDBI"


def _send_via_cpaas(candidate: ReEngagementCandidate) -> None:
    webhook = os.getenv("CPAAS_WEBHOOK_URL", "")
    if not webhook:
        log.info("[CPaaS mock] Would send to %s: %s", candidate.name, candidate.sms_script[:60])
        return
    import urllib.request
    payload = json.dumps({
        "to": candidate.prospect_id,  # real impl: phone number
        "message": candidate.whatsapp_script,
    }).encode()
    req = urllib.request.Request(webhook, data=payload, headers={"Content-Type": "application/json"})
    urllib.request.urlopen(req, timeout=5)


class ColdProspectReEngagementAgent:
    """Scan pipeline for disengaged prospects and generate re-engagement actions."""

    name = "reengagement_agent"

    def find_candidates(self, prospects: list[dict], top_n: int = 5) -> list[ReEngagementCandidate]:
        cold = [p for p in prospects if p.get("lead_band") in COLD_BANDS]
        scored = sorted(cold, key=_urgency, reverse=True)[:top_n]

        return [
            ReEngagementCandidate(
                prospect_id=p["prospect_id"],
                name=p.get("name", ""),
                segment=p.get("segment", ""),
                lead_band=p.get("lead_band", ""),
                lead_score=p.get("lead_score", 0),
                life_event=(p.get("life_event") or "").replace("_", " "),
                recommended_product=p.get("recommended_product", ""),
                days_since_contact=p.get("last_interaction_days", 0),
                urgency_score=_urgency(p),
                whatsapp_script=_whatsapp_script(p),
                sms_script=_sms_script(p),
            )
            for p in scored
        ]

    def send(self, candidate: ReEngagementCandidate) -> dict:
        """Dispatch via CPaaS (or log if CPAAS_WEBHOOK_URL not set)."""
        try:
            _send_via_cpaas(candidate)
            return {"status": "sent", "prospect_id": candidate.prospect_id}
        except Exception as e:
            log.error("CPaaS send failed for %s: %s", candidate.prospect_id, e)
            return {"status": "failed", "error": str(e), "prospect_id": candidate.prospect_id}
