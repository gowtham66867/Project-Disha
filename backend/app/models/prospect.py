from __future__ import annotations

from sqlalchemy import Float, Integer, String, Boolean, JSON
from sqlalchemy.orm import Mapped, mapped_column

from ..db import Base


class Prospect(Base):
    __tablename__ = "prospects"

    prospect_id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String)
    age: Mapped[int] = mapped_column(Integer, default=0)
    city: Mapped[str] = mapped_column(String, default="")
    state: Mapped[str] = mapped_column(String, default="")
    segment: Mapped[str] = mapped_column(String, default="")
    annual_income: Mapped[float] = mapped_column(Float, default=0.0)
    existing_customer: Mapped[bool] = mapped_column(Boolean, default=False)
    digital_activity_score: Mapped[int] = mapped_column(Integer, default=0)
    last_interaction_days: Mapped[int] = mapped_column(Integer, default=0)
    life_event: Mapped[str] = mapped_column(String, default="")
    credit_bureau_score: Mapped[int] = mapped_column(Integer, default=0)
    employer_category: Mapped[str] = mapped_column(String, default="")
    loan_enquiries_6m: Mapped[int] = mapped_column(Integer, default=0)
    upi_monthly_txn: Mapped[int] = mapped_column(Integer, default=0)
    rm_id: Mapped[str] = mapped_column(String, default="", index=True)

    # Computed fields (filled by scorer)
    lead_score: Mapped[float] = mapped_column(Float, default=0.0)
    lead_band: Mapped[str] = mapped_column(String, default="")
    recommended_product: Mapped[str] = mapped_column(String, default="")
    recommended_channel: Mapped[str] = mapped_column(String, default="")
    recommended_timing: Mapped[str] = mapped_column(String, default="")
    pipeline_stage: Mapped[str] = mapped_column(String, default="New")
    score_version: Mapped[str] = mapped_column(String, default="")
