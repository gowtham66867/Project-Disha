"""IDBI CRM Sandbox adapter — stub wired for real endpoints.

Set DATA_SOURCE=idbi_sandbox and IDBI_SANDBOX_BASE_URL + IDBI_SANDBOX_API_KEY
to activate.  Every _fetch_* method raises NotImplementedError naming the
real endpoint so the handover to IDBI's sandbox team is a drop-in.
"""
from __future__ import annotations

import os

from .base import ProspectDataAdapter


class SandboxNotConfigured(RuntimeError):
    pass


class IDBISandboxAdapter(ProspectDataAdapter):
    name = "idbi_sandbox"

    def __init__(self) -> None:
        self._base = os.getenv("IDBI_SANDBOX_BASE_URL", "")
        self._key = os.getenv("IDBI_SANDBOX_API_KEY", "")
        if not self._base or not self._key:
            raise SandboxNotConfigured(
                "Set IDBI_SANDBOX_BASE_URL and IDBI_SANDBOX_API_KEY to use the sandbox."
            )

    def fetch_all(self) -> list[dict]:
        raw = self._fetch_crm_prospects()
        enriched = []
        for p in raw:
            p["credit_bureau_score"] = self._fetch_bureau_score(p["prospect_id"])
            p["upi_monthly_txn"] = self._fetch_upi_summary(p["prospect_id"])
            enriched.append(p)
        return enriched

    def _fetch_crm_prospects(self) -> list[dict]:
        # GET {base}/api/v1/crm/prospects
        raise NotImplementedError("Implement: GET /api/v1/crm/prospects")

    def _fetch_bureau_score(self, prospect_id: str) -> int:
        # GET {base}/api/v1/bureau/score?id={prospect_id}
        raise NotImplementedError(f"Implement: GET /api/v1/bureau/score?id={prospect_id}")

    def _fetch_upi_summary(self, prospect_id: str) -> int:
        # GET {base}/api/v1/upi/summary?id={prospect_id}
        raise NotImplementedError(f"Implement: GET /api/v1/upi/summary?id={prospect_id}")
