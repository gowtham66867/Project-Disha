"""Append-only audit log for every RM interaction and copilot query.

Immutability is enforced at two layers:
1. ORM level — before_update/before_delete listeners raise InteractionImmutableError
2. Database level — db_guards.py installs SQLite RAISE(ABORT) / PostgreSQL
   trigger function that rejects raw SQL mutations against the table.
"""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Integer, String, Text, event
from sqlalchemy.orm import Mapped, mapped_column

from ..db import Base


class InteractionImmutableError(RuntimeError):
    """Raised when any code path attempts to modify or delete an interaction row."""


class ProspectInteractionLog(Base):
    __tablename__ = "prospect_interaction_log"

    log_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    prospect_id: Mapped[str] = mapped_column(String, index=True)
    rm_id: Mapped[str] = mapped_column(String, default="")
    event_type: Mapped[str] = mapped_column(String)  # score_computed | nba_generated | copilot_query | stage_changed
    event_detail: Mapped[str] = mapped_column(Text, default="")
    lead_score_snapshot: Mapped[float] = mapped_column(default=0.0)
    score_version: Mapped[str] = mapped_column(String, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)


@event.listens_for(ProspectInteractionLog, "before_update")
def _reject_update(mapper, connection, target):
    raise InteractionImmutableError("prospect_interaction_log is append-only — rows cannot be modified.")


@event.listens_for(ProspectInteractionLog, "before_delete")
def _reject_delete(mapper, connection, target):
    raise InteractionImmutableError("prospect_interaction_log is append-only — rows cannot be deleted.")
