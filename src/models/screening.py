"""Screening events and screening observations."""
from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import Date, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import Base, utcnow


class ScreeningEvent(Base):
    __tablename__ = "screening_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    event_code: Mapped[str] = mapped_column(String(20), unique=True, index=True)
    programme_id: Mapped[int] = mapped_column(ForeignKey("programmes.id"), index=True)
    facility_id: Mapped[int] = mapped_column(ForeignKey("facilities.id"), index=True)
    event_name: Mapped[str] = mapped_column(String(160))
    event_date: Mapped[date] = mapped_column(Date)
    status: Mapped[str] = mapped_column(String(30), default="Planned")
    attendance_count: Mapped[int] = mapped_column(Integer, default=0)

    screenings: Mapped[list["Screening"]] = relationship(
        back_populates="event", cascade="all, delete-orphan", lazy="selectin"
    )


class Screening(Base):
    __tablename__ = "screenings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    participant_id: Mapped[int] = mapped_column(ForeignKey("participants.id"), index=True)
    event_id: Mapped[int] = mapped_column(ForeignKey("screening_events.id"), index=True)
    screening_type: Mapped[str] = mapped_column(String(120))
    observation_text: Mapped[str] = mapped_column(Text, default="")
    result_category: Mapped[str] = mapped_column(String(40), default="Needs clinician review")
    review_status: Mapped[str] = mapped_column(String(40), default="Pending clinician review")
    reviewed_by: Mapped[str | None] = mapped_column(String(80), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)

    event: Mapped["ScreeningEvent"] = relationship(back_populates="screenings")
