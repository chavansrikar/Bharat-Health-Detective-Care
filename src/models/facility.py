"""Facility, service and infrastructure models."""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import Base, utcnow


class Facility(Base):
    __tablename__ = "facilities"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    code: Mapped[str] = mapped_column(String(24), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(180), index=True)
    type: Mapped[str] = mapped_column(String(90), index=True)
    state: Mapped[str] = mapped_column(String(80), default="Telangana (illustrative)", index=True)
    district: Mapped[str] = mapped_column(String(90), default="Yadadri Bhuvanagiri", index=True)
    mandal: Mapped[str] = mapped_column(String(90), index=True)
    locality: Mapped[str] = mapped_column(String(140))
    latitude: Mapped[float] = mapped_column(Float, default=17.5)
    longitude: Mapped[float] = mapped_column(Float, default=78.9)
    address_label: Mapped[str] = mapped_column(String(220), default="")
    phone_placeholder: Mapped[str] = mapped_column(String(50), default="Not published in demo")
    ownership: Mapped[str] = mapped_column(String(60), default="Government")
    beds: Mapped[int] = mapped_column(Integer, default=0)
    catchment_population: Mapped[int] = mapped_column(Integer, default=0)
    verification_status: Mapped[str] = mapped_column(String(40), default="Pending verification", index=True)
    operating_status: Mapped[str] = mapped_column(String(40), default="Operational", index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    capacity_notes: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow)

    services: Mapped[list["Service"]] = relationship(
        back_populates="facility", cascade="all, delete-orphan", lazy="selectin"
    )


class Service(Base):
    __tablename__ = "services"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    facility_id: Mapped[int] = mapped_column(ForeignKey("facilities.id"), index=True)
    service_name: Mapped[str] = mapped_column(String(140), index=True)
    category: Mapped[str] = mapped_column(String(90), default="General")
    availability_note: Mapped[str] = mapped_column(String(220), default="Confirm by phone")
    capacity_per_period: Mapped[int] = mapped_column(Integer, default=0)
    active: Mapped[bool] = mapped_column(Boolean, default=True)

    facility: Mapped["Facility"] = relationship(back_populates="services")
