"""Model registry — import all models so SQLAlchemy knows the metadata."""
from src.models.base import Base, utcnow
from src.models.citizen import Appointment
from src.models.facility import Facility, Service
from src.models.operations import AuditEvent, Campaign, Notification, SubstanceUseCase
from src.models.participant import Participant, Programme, Staff
from src.models.referral import LabOrder, Referral
from src.models.screening import Screening, ScreeningEvent
from src.models.workforce import EmploymentApplication, StaffVacancy

__all__ = [
    "Base",
    "utcnow",
    "Facility",
    "Service",
    "Participant",
    "Programme",
    "Staff",
    "Referral",
    "LabOrder",
    "Screening",
    "ScreeningEvent",
    "AuditEvent",
    "Campaign",
    "Notification",
    "SubstanceUseCase",
    "StaffVacancy",
    "EmploymentApplication",
    "Appointment",
]
