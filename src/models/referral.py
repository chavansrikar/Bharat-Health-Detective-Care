"""Referral coordination and laboratory workflow models."""
from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import Date, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import Base, utcnow


class Referral(Base):
    __tablename__ = "referrals"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    referral_code: Mapped[str] = mapped_column(String(28), unique=True, index=True)
    participant_id: Mapped[int] = mapped_column(ForeignKey("participants.id"), index=True)
    screening_id: Mapped[int | None] = mapped_column(ForeignKey("screenings.id"), nullable=True)
    source_facility_id: Mapped[int] = mapped_column(ForeignKey("facilities.id"), index=True)
    destination_facility_id: Mapped[int] = mapped_column(ForeignKey("facilities.id"), index=True)
    reason_category: Mapped[str] = mapped_column(String(160))
    priority: Mapped[str] = mapped_column(String(40), default="Routine")
    status: Mapped[str] = mapped_column(String(50), default="Draft", index=True)
    referring_doctor: Mapped[str] = mapped_column(String(90), default="Demo clinician")
    created_by: Mapped[str] = mapped_column(String(90), default="Demo user")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    follow_up_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    closed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    closure_note: Mapped[str] = mapped_column(Text, default="")

    lab_orders: Mapped[list["LabOrder"]] = relationship(
        back_populates="referral", cascade="all, delete-orphan", lazy="selectin"
    )


class LabOrder(Base):
    __tablename__ = "lab_orders"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    order_code: Mapped[str] = mapped_column(String(28), unique=True, index=True)
    referral_id: Mapped[int] = mapped_column(ForeignKey("referrals.id"), index=True)
    lab_facility_id: Mapped[int] = mapped_column(ForeignKey("facilities.id"), index=True)
    test_category: Mapped[str] = mapped_column(String(160))
    priority: Mapped[str] = mapped_column(String(40), default="Routine")
    requested_by: Mapped[str] = mapped_column(String(90), default="Demo clinician")
    sample_status: Mapped[str] = mapped_column(String(50), default="Ordered")
    result_status: Mapped[str] = mapped_column(String(70), default="Pending")
    report_status: Mapped[str] = mapped_column(String(70), default="Pending result entry")
    reviewer_status: Mapped[str] = mapped_column(String(80), default="Awaiting clinician review")
    demo_result_note: Mapped[str] = mapped_column(String(200), default="Demo status only — no clinical value")
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow)

    referral: Mapped["Referral"] = relationship(back_populates="lab_orders")
