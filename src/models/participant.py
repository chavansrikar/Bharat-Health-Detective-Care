"""Synthetic participant, workforce and programme models."""
from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import Date, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from src.models.base import Base, utcnow


class Participant(Base):
    __tablename__ = "participants"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    synthetic_code: Mapped[str] = mapped_column(String(24), unique=True, index=True)
    display_name_alias: Mapped[str] = mapped_column(String(90))
    age_band: Mapped[str] = mapped_column(String(20))
    gender: Mapped[str] = mapped_column(String(30), default="Not recorded")
    locality: Mapped[str] = mapped_column(String(140))
    district: Mapped[str] = mapped_column(String(90), default="Yadadri Bhuvanagiri")
    consent_status: Mapped[str] = mapped_column(String(40), default="Granted (demo)")
    assigned_worker: Mapped[str] = mapped_column(String(90), default="Unassigned")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


class Staff(Base):
    __tablename__ = "staff"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    staff_code: Mapped[str] = mapped_column(String(24), unique=True, index=True)
    display_name: Mapped[str] = mapped_column(String(90))
    role: Mapped[str] = mapped_column(String(90), index=True)
    qualification: Mapped[str] = mapped_column(String(120), default="Demo credential")
    facility_id: Mapped[int | None] = mapped_column(ForeignKey("facilities.id"), nullable=True, index=True)
    skills: Mapped[str] = mapped_column(String(200), default="")
    availability: Mapped[str] = mapped_column(String(50), default="Available")
    shift: Mapped[str] = mapped_column(String(50), default="Day")
    employment_type: Mapped[str] = mapped_column(String(50), default="Regular")
    verification_status: Mapped[str] = mapped_column(String(50), default="Pending verification")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


class Programme(Base):
    __tablename__ = "programmes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(180))
    description: Mapped[str] = mapped_column(Text, default="")
    cohort_text: Mapped[str] = mapped_column(String(240), default="")
    eligibility_notes: Mapped[str] = mapped_column(Text, default="")
    guidance_reference: Mapped[str] = mapped_column(String(240), default="Confirm with local clinical authority")
    start_date: Mapped[date] = mapped_column(Date)
    end_date: Mapped[date] = mapped_column(Date)
    status: Mapped[str] = mapped_column(String(40), default="Active")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
