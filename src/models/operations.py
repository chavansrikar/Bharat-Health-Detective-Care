"""Awareness campaigns, notifications, substance-use cases and audit events."""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from src.models.base import Base, utcnow


class Campaign(Base):
    __tablename__ = "campaigns"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(180))
    message: Mapped[str] = mapped_column(Text, default="")
    language: Mapped[str] = mapped_column(String(50), default="Telugu")
    audience: Mapped[str] = mapped_column(String(140), default="General community")
    target_area: Mapped[str] = mapped_column(String(140))
    planned_channel: Mapped[str] = mapped_column(String(60), default="Planned SMS")
    schedule_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    status: Mapped[str] = mapped_column(String(50), default="Draft")
    responsible_facility_id: Mapped[int | None] = mapped_column(ForeignKey("facilities.id"), nullable=True)
    delivery_status: Mapped[str] = mapped_column(String(70), default="Simulated — not sent")
    created_by: Mapped[str] = mapped_column(String(90), default="Demo user")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


class Notification(Base):
    __tablename__ = "notifications"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(180))
    message: Mapped[str] = mapped_column(Text, default="")
    audience: Mapped[str] = mapped_column(String(160), default="Facility administrators")
    channel: Mapped[str] = mapped_column(String(60), default="Planned SMS")
    status: Mapped[str] = mapped_column(String(50), default="Draft")
    related_entity: Mapped[str] = mapped_column(String(80), default="")
    schedule_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    created_by: Mapped[str] = mapped_column(String(90), default="Demo user")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


class AuditEvent(Base):
    """Lightweight in-app activity log for demo accountability."""

    __tablename__ = "audit_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    actor_role: Mapped[str] = mapped_column(String(90), default="Demo user")
    action: Mapped[str] = mapped_column(String(180))
    entity_type: Mapped[str] = mapped_column(String(60), default="")
    entity_id: Mapped[str] = mapped_column(String(60), default="")
    note: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


class SubstanceUseCase(Base):
    """Voluntary, confidential demo case. No punitive or enforcement use."""

    __tablename__ = "substance_use_cases"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    case_code: Mapped[str] = mapped_column(String(28), unique=True, index=True)
    participant_id: Mapped[int] = mapped_column(ForeignKey("participants.id"), index=True)
    substance_category: Mapped[str] = mapped_column(String(120))
    screening_note: Mapped[str] = mapped_column(Text, default="")
    consent_status: Mapped[str] = mapped_column(String(50), default="Granted (demo)")
    confidentiality_level: Mapped[str] = mapped_column(String(60), default="Restricted — counselling team only")
    counselling_status: Mapped[str] = mapped_column(String(60), default="Screening recorded")
    assigned_counsellor: Mapped[str] = mapped_column(String(90), default="Unassigned")
    follow_up_date: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow)
