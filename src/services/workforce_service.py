"""Medical workforce, vacancy and healthcare-employment operations."""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from src.config import APPLICATION_STATUSES, VACANCY_PRIORITIES, VACANCY_STATUSES
from src.models import EmploymentApplication, Facility, Staff, StaffVacancy
from src.models.base import utcnow


def list_staff(
    session: Session,
    facility_ids: list[int] | None = None,
    role: str = "All",
    availability: str = "All",
    text: str = "",
) -> list[dict]:
    facility_names = dict(session.execute(select(Facility.id, Facility.name)).all())
    stmt = select(Staff).order_by(Staff.role, Staff.display_name)
    if facility_ids is not None:
        stmt = stmt.where(Staff.facility_id.in_(facility_ids))
    if role and role != "All":
        stmt = stmt.where(Staff.role == role)
    if availability and availability != "All":
        stmt = stmt.where(Staff.availability == availability)
    if text:
        like = f"%{text.strip().lower()}%"
        stmt = stmt.where(or_(func.lower(Staff.display_name).like(like), func.lower(Staff.skills).like(like)))
    rows = session.scalars(stmt).all()
    return [
        {
            "staff_id": s.id, "staff_code": s.staff_code, "name": s.display_name,
            "role": s.role, "qualification": s.qualification,
            "facility": facility_names.get(s.facility_id, "Unassigned"),
            "skills": s.skills, "availability": s.availability, "shift": s.shift,
            "employment_type": s.employment_type, "verification": s.verification_status,
        }
        for s in rows
    ]


def list_vacancies(
    session: Session,
    facility_ids: list[int] | None = None,
    status: str = "All",
    priority: str = "All",
    role: str = "All",
) -> list[dict]:
    facility_names = dict(session.execute(select(Facility.id, Facility.name)).all())
    stmt = select(StaffVacancy).order_by(StaffVacancy.priority, StaffVacancy.role)
    if facility_ids is not None:
        stmt = stmt.where(StaffVacancy.facility_id.in_(facility_ids))
    if status and status != "All":
        stmt = stmt.where(StaffVacancy.status == status)
    if priority and priority != "All":
        stmt = stmt.where(StaffVacancy.priority == priority)
    if role and role != "All":
        stmt = stmt.where(StaffVacancy.role == role)
    rows = session.scalars(stmt).all()
    return [
        {
            "vacancy_id": v.id, "vacancy_code": v.vacancy_code,
            "facility": facility_names.get(v.facility_id, ""),
            "facility_id": v.facility_id, "role": v.role,
            "required": v.required_count, "filled": v.filled_count, "gap": v.gap,
            "status": v.status, "priority": v.priority, "notes": v.notes,
        }
        for v in rows
    ]


def vacancy_choices(session: Session) -> list[tuple[str, int]]:
    return [(v["vacancy_code"] + " — " + v["role"], v["vacancy_id"]) for v in list_vacancies(session)]


def create_vacancy(
    session: Session,
    facility_id: int,
    role: str,
    required_count: int,
    priority: str = "Routine",
    notes: str = "",
) -> StaffVacancy:
    if session.get(Facility, facility_id) is None:
        raise ValueError("Choose a valid facility")
    if not role.strip():
        raise ValueError("Role is required")
    if required_count < 1:
        raise ValueError("Required count must be at least 1")
    if priority not in VACANCY_PRIORITIES:
        raise ValueError("Invalid priority")
    count = int(session.scalar(select(func.count()).select_from(StaffVacancy)) or 0)
    vacancy = StaffVacancy(
        vacancy_code=f"VAC-{count + 1:04d}", facility_id=facility_id,
        role=role.strip(), required_count=int(required_count),
        filled_count=0, priority=priority, notes=notes.strip(), status="Open",
    )
    session.add(vacancy)
    session.flush()
    return vacancy


def update_vacancy(session: Session, vacancy_id: int, filled_count: int | None = None, status: str | None = None) -> StaffVacancy:
    vacancy = session.get(StaffVacancy, vacancy_id)
    if vacancy is None:
        raise ValueError("Vacancy not found")
    if filled_count is not None:
        if filled_count < 0:
            raise ValueError("Filled count cannot be negative")
        vacancy.filled_count = min(int(filled_count), vacancy.required_count)
    if status in VACANCY_STATUSES:
        vacancy.status = status
    if vacancy.gap == 0 and status is None:
        vacancy.status = "Filled"
    session.flush()
    return vacancy


def list_applications(
    session: Session,
    facility_ids: list[int] | None = None,
    status: str = "All",
    role: str = "All",
) -> list[dict]:
    facility_names = dict(session.execute(select(Facility.id, Facility.name)).all())
    stmt = select(EmploymentApplication).order_by(EmploymentApplication.applied_at.desc())
    if facility_ids is not None:
        stmt = stmt.where(EmploymentApplication.facility_id.in_(facility_ids))
    if status and status != "All":
        stmt = stmt.where(EmploymentApplication.status == status)
    if role and role != "All":
        stmt = stmt.where(EmploymentApplication.role == role)
    rows = session.scalars(stmt).all()
    return [
        {
            "application_id": a.id, "application_code": a.application_code,
            "applicant": a.applicant_alias, "role": a.role,
            "facility": facility_names.get(a.facility_id, ""),
            "qualification": a.qualification, "experience_years": a.experience_years,
            "status": a.status, "applied_at": a.applied_at.strftime("%Y-%m-%d"),
        }
        for a in rows
    ]


def create_application(
    session: Session,
    applicant_alias: str,
    role: str,
    facility_id: int | None = None,
    qualification: str = "",
    experience_years: int = 0,
    notes: str = "",
) -> EmploymentApplication:
    if not applicant_alias.strip():
        raise ValueError("Applicant alias is required")
    if not role.strip():
        raise ValueError("Role is required")
    count = int(session.scalar(select(func.count()).select_from(EmploymentApplication)) or 0)
    application = EmploymentApplication(
        application_code=f"APP-{count + 1:04d}", applicant_alias=applicant_alias.strip(),
        role=role.strip(), facility_id=facility_id,
        qualification=qualification.strip() or "Demo qualification",
        experience_years=max(0, int(experience_years)),
        status="Received", notes=notes.strip(), applied_at=utcnow(),
    )
    session.add(application)
    session.flush()
    return application


def update_application_status(session: Session, application_id: int, status: str) -> EmploymentApplication:
    application = session.get(EmploymentApplication, application_id)
    if application is None:
        raise ValueError("Application not found")
    if status not in APPLICATION_STATUSES:
        raise ValueError("Invalid application status")
    application.status = status
    session.flush()
    return application


def workforce_summary(session: Session, facility_ids: list[int] | None = None) -> dict[str, int]:
    staff = session.scalars(
        select(Staff) if facility_ids is None else select(Staff).where(Staff.facility_id.in_(facility_ids))
    ).all()
    vacancies = session.scalars(
        select(StaffVacancy) if facility_ids is None else select(StaffVacancy).where(StaffVacancy.facility_id.in_(facility_ids))
    ).all()
    applications = session.scalars(
        select(EmploymentApplication)
        if facility_ids is None
        else select(EmploymentApplication).where(EmploymentApplication.facility_id.in_(facility_ids))
    ).all()
    return {
        "staff_total": len(staff),
        "available": sum(1 for s in staff if s.availability in {"Available", "On duty"}),
        "on_leave": sum(1 for s in staff if s.availability == "On leave"),
        "open_vacancies": sum(1 for v in vacancies if v.status == "Open"),
        "vacancy_gap": sum(v.gap for v in vacancies),
        "applications_received": len(applications),
        "applications_pending": sum(1 for a in applications if a.status in {"Received", "Shortlisted", "Interview scheduled"}),
        "hired": sum(1 for a in applications if a.status == "Offer"),
    }


def facility_staffing_rows(session: Session, facility_ids: list[int] | None = None) -> list[dict]:
    stmt = select(Facility).order_by(Facility.name)
    if facility_ids is not None:
        stmt = stmt.where(Facility.id.in_(facility_ids))
    facilities = session.scalars(stmt).all()
    staff_counts: dict[int, int] = {}
    vacancy_gaps: dict[int, int] = {}
    for facility in facilities:
        staff_counts[facility.id] = int(session.scalar(
            select(func.count()).select_from(Staff).where(Staff.facility_id == facility.id)
        ) or 0)
        gaps = session.scalars(select(StaffVacancy).where(StaffVacancy.facility_id == facility.id)).all()
        vacancy_gaps[facility.id] = sum(v.gap for v in gaps)
    return [
        {
            "facility": f.name, "district": f.district, "mandal": f.mandal,
            "staff": staff_counts[f.id], "vacancy_gap": vacancy_gaps[f.id],
            "status": "Needs attention" if vacancy_gaps[f.id] else "Adequate in demo",
        }
        for f in facilities
    ]
