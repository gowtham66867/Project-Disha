from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional


class ProspectDataAdapter(ABC):
    """Contract for any prospect data source.

    Implement this to plug in a real CRM (Salesforce, IDBI CRM API,
    bureau feed) without touching scoring, NBA, or the frontend.
    """

    name: str = "base"

    @abstractmethod
    def fetch_all(self) -> list[dict]:
        """Return all prospects as plain dicts."""

    def fetch_one(self, prospect_id: str) -> Optional[dict]:
        for p in self.fetch_all():
            if p.get("prospect_id") == prospect_id:
                return p
        return None
