"""Workforce vacancies and employment applications."""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from src.models.base import Base, utcnow


class StaffVacancy(Base):
    __tablename__ = "staff_vacancies"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    vacancy_code: Mapped[str] = mapped_column(String(28), unique=True, index=True)
    facility_id: Mapped[int] = mapped_column(ForeignKey("facilities.id"), index=True)
    role: Mapped[str] = mapped_column(String(90), index=True)
    required_count: Mapped[int] = mapped_column(Integer, default=1)
    filled_count: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(String(40), default="Open")
    priority: Mapped[str] = mapped_column(String(40), default="Routine")
    notes: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)

    @property
    def gap(self) -> int:
        return max(self.required_count - self.filled_count, 0)


class EmploymentApplication(Base):
    __tablename__ = "employment_applications"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    application_code: Mapped[str] = mapped_column(String(28), unique=True, index=True)
    applicant_alias: Mapped[str] = mapped_column(String(90))
    role: Mapped[str] = mapped_column(String(90), index=True)
    facility_id: Mapped[int | None] = mapped_column(ForeignKey("facilities.id"), nullable=True)
    qualification: Mapped[str] = mapped_column(String(140), default="Demo qualification")
    experience_years: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(String(50), default="Received", index=True)
    notes: Mapped[str] = mapped_column(Text, default="")
    applied_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
