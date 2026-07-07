from __future__ import annotations

import json
import os
from typing import Optional

from .base import ProspectDataAdapter


class SyntheticFileAdapter(ProspectDataAdapter):
    """Reads prospects from a local JSON fixture (zero-infra demo)."""

    name = "synthetic"

    def __init__(self, path: str = "mock-data/prospects.json") -> None:
        self._path = path

    def fetch_all(self) -> list[dict]:
        if not os.path.exists(self._path):
            return []
        with open(self._path) as f:
            return json.load(f)
