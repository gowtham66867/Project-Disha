"""Episodic memory — persists RM ↔ Disha conversation history per prospect.

Injected as context on each new query so the copilot can reference earlier
exchanges ("As I mentioned before, Priya's bureau score is the key driver…").
Append-only by ORM convention; no update/delete routes exist.
"""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from ..db import Base


class CopilotMemory(Base):
    __tablename__ = "copilot_memory"

    memory_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    prospect_id: Mapped[str] = mapped_column(String, index=True, default="")
    rm_id: Mapped[str] = mapped_column(String, default="")
    role: Mapped[str] = mapped_column(String)          # "user" | "assistant"
    content: Mapped[str] = mapped_column(Text)
    provider: Mapped[str] = mapped_column(String, default="")  # which LLM answered
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
