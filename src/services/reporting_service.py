"""Aggregated metrics, operational analytics and CSV exports.

Every figure is computed from the local demo database. Filters apply to the
facility scope; dependent operational records are scoped through their facility.
"""
from __future__ import annotations

from datetime import date

import pandas as pd
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from src.config import REFERRAL_TRANSITIONS
from src.models import (
    Appointment,
    Campaign,
    EmploymentApplication,
    Facility,
    LabOrder,
    Notification,
    Referral,
    Screening,
    ScreeningEvent,
    Service,
    Staff,
    StaffVacancy,
    SubstanceUseCase,
)
from src.services import facility_service

OPEN_REFERRAL_STATUSES = {"Draft", "Sent", "Accepted", "Scheduled", "Returned for clarification"}


# ---------------------------------------------------------------------------
# Scope helpers
# ---------------------------------------------------------------------------
def scope_ids(
    session: Session,
    state: str = "All",
    district: str = "All",
    mandal: str = "All",
    category: str = "All",
    active: str = "All",
) -> list[int]:
    return facility_service.filtered_facility_ids(
        session, state=state, district=district, mandal=mandal, category=category, active=active
    )


def _facilities(session: Session, ids: list[int]) -> list[Facility]:
    if not ids:
        return []
    return list(session.scalars(select(Facility).where(Facility.id.in_(ids)).order_by(Facility.name)).all())


def _avg_utilization(session: Session, ids: list[int]) -> float:
    rows = [
        r for r in facility_service.utilization_rows(session, facility_ids=ids)
        if r["configured_capacity"] > 0 and r["completed_sessions"] > 0
    ]
    return round(sum(r["utilization_pct"] for r in rows) / len(rows), 1) if rows else 0.0


def _staffing_gaps(session: Session, ids: list[int]) -> int:
    if not ids:
        return 0
    rows = session.scalars(select(StaffVacancy).where(StaffVacancy.facility_id.in_(ids))).all()
    return sum(max(v.required_count - v.filled_count, 0) for v in rows)


def overview_kpis(
    session: Session,
    state: str = "All",
    district: str = "All",
    mandal: str = "All",
    category: str = "All",
    active: str = "All",
) -> dict[str, float]:
    ids = scope_ids(session, state, district, mandal, category, active)
    facilities = _facilities(session, ids)
    total = len(facilities)
    active_count = sum(1 for f in facilities if f.is_active)
    inactive_count = total - active_count

    services = int(session.scalar(
        select(func.count()).select_from(Service).where(Service.facility_id.in_(ids), Service.active.is_(True))
    ) or 0) if ids else 0

    staff_rows = session.scalars(select(Staff).where(Staff.facility_id.in_(ids))).all() if ids else []
    staff_total = len(staff_rows)
    staff_available = sum(1 for s in staff_rows if s.availability in {"Available", "On duty"})

    event_ids = list(session.scalars(select(ScreeningEvent.id).where(ScreeningEvent.facility_id.in_(ids))).all()) if ids else []
    screening_events = len(event_ids)
    screenings = int(session.scalar(
        select(func.count()).select_from(Screening).where(Screening.event_id.in_(event_ids))
    ) or 0) if event_ids else 0
    pending_reviews = int(session.scalar(
        select(func.count()).select_from(Screening).where(
            Screening.event_id.in_(event_ids), Screening.review_status == "Pending clinician review"
        )
    ) or 0) if event_ids else 0

    referrals = session.scalars(select(Referral).where(Referral.source_facility_id.in_(ids))).all() if ids else []
    referrals_total = len(referrals)
    referrals_open = sum(1 for r in referrals if r.status in OPEN_REFERRAL_STATUSES)
    sent = [r for r in referrals if r.status not in {"Draft", "Cancelled"}]
    completed = [r for r in referrals if r.status == "Completed"]
    completion = round((len(completed) / len(sent)) * 100, 1) if sent else 0.0
    followup_due = [r for r in referrals if r.follow_up_date and r.status not in {"Draft", "Cancelled"}]
    followup_completed = [r for r in followup_due if r.status == "Completed"]
    followup_rate = round((len(followup_completed) / len(followup_due)) * 100, 1) if followup_due else 0.0
    today = date.today()
    overdue = sum(
        1 for r in referrals
        if r.follow_up_date and r.follow_up_date < today
        and r.status in {"Sent", "Accepted", "Scheduled", "Returned for clarification"}
    )

    lab_orders = session.scalars(select(LabOrder).where(LabOrder.lab_facility_id.in_(ids))).all() if ids else []
    pending_reports = sum(1 for o in lab_orders if o.report_status != "Delivered")
    lab_awaiting_review = sum(1 for o in lab_orders if o.reviewer_status == "Awaiting clinician review")

    catchment_total = sum(f.catchment_population for f in facilities)
    catchment_covered = sum(f.catchment_population for f in facilities if f.is_active)
    coverage = round((catchment_covered / catchment_total) * 100, 1) if catchment_total else 0.0

    pending_verification = sum(1 for f in facilities if f.verification_status != "Verified")
    utilization = _avg_utilization(session, ids)
    staffing_gaps = _staffing_gaps(session, ids)
    reviewed = int(session.scalar(
        select(func.count()).select_from(Screening).where(
            Screening.event_id.in_(event_ids), Screening.review_status == "Reviewed"
        )
    ) or 0) if event_ids else 0
    review_pct = round((reviewed / screenings) * 100, 1) if screenings else 0.0

    return {
        "facilities": total,
        "total_facilities": total,
        "active_facilities": active_count,
        "inactive_facilities": inactive_count,
        "utilization_pct": utilization,
        "services": services,
        "staff_total": staff_total,
        "staff_available": staff_available,
        "workforce": staff_total,
        "screening_events": screening_events,
        "screening_activities": screenings,
        "screenings": screenings,
        "screening_review_pct": review_pct,
        "pending_reports": pending_reports,
        "lab_awaiting_review": lab_awaiting_review,
        "referrals_total": referrals_total,
        "referrals_open": referrals_open,
        "referral_completion_pct": completion,
        "followup_completion_pct": followup_rate,
        "coverage_pct": coverage,
        "staffing_gaps": staffing_gaps,
        "pending_reviews": pending_reviews,
        "pending_verification": pending_verification,
        "followups_overdue": overdue,
    }


def dashboard_kpis(session: Session) -> dict[str, int]:
    """Backward-compatible unfiltered snapshot."""
    return overview_kpis(session)


# ---------------------------------------------------------------------------
# Alerts and access gaps
# ---------------------------------------------------------------------------
def access_gap_rows(
    session: Session,
    state: str = "All",
    district: str = "All",
    mandal: str = "All",
    category: str = "All",
    active: str = "All",
) -> list[dict]:
    ids = scope_ids(session, state, district, mandal, category, active)
    facilities = _facilities(session, ids)
    from src.config import MANDALS_BY_DISTRICT

    districts = [district] if district and district != "All" else list(MANDALS_BY_DISTRICT.keys())
    rows = []
    for dist in districts:
        for m in MANDALS_BY_DISTRICT.get(dist, []):
            active_here = [f for f in facilities if f.district == dist and f.mandal == m and f.is_active]
            primary_plus = [
                f for f in active_here
                if facility_service.category_of(f) in {"Primary care", "Secondary care", "Tertiary care"}
            ]
            if not active_here:
                status = "No active facility"
            elif not primary_plus:
                status = "No active PHC/CHC/hospital"
            else:
                status = "Covered"
            rows.append({
                "district": dist,
                "mandal": m,
                "active_facilities": len(active_here),
                "primary_or_higher": len(primary_plus),
                "status": status,
            })
    return rows


def operational_alerts(
    session: Session,
    state: str = "All",
    district: str = "All",
    mandal: str = "All",
    category: str = "All",
    active: str = "All",
) -> list[dict]:
    kpis = overview_kpis(session, state, district, mandal, category, active)
    alerts: list[dict] = []
    if kpis["inactive_facilities"]:
        alerts.append({"level": "High", "text": f"{kpis['inactive_facilities']} facility record(s) are inactive in the selected scope."})
    if kpis["followups_overdue"]:
        alerts.append({"level": "High", "text": f"{kpis['followups_overdue']} referral follow-up(s) overdue — review referral coordination."})
    if kpis["staffing_gaps"]:
        alerts.append({"level": "High", "text": f"{kpis['staffing_gaps']} unfilled critical post(s) recorded — review workforce deployment."})
    if kpis["pending_reports"]:
        alerts.append({"level": "Medium", "text": f"{kpis['pending_reports']} diagnostic report(s) not yet delivered."})
    if kpis["lab_awaiting_review"]:
        alerts.append({"level": "Medium", "text": f"{kpis['lab_awaiting_review']} laboratory result(s) awaiting clinician review."})
    if kpis["pending_reviews"]:
        alerts.append({"level": "Medium", "text": f"{kpis['pending_reviews']} screening observation(s) pending clinician review — not diagnoses."})
    if kpis["pending_verification"]:
        alerts.append({"level": "Medium", "text": f"{kpis['pending_verification']} facility record(s) pending verification."})
    gaps = [r for r in access_gap_rows(session, state, district, mandal, category, active) if r["status"] != "Covered"]
    if gaps:
        alerts.append({"level": "Info", "text": f"{len(gaps)} mandal/mandals show an access gap in the demo coverage view."})
    spare = [r for r in facility_service.utilization_rows(session, facility_ids=scope_ids(session, state, district, mandal, category, active)) if r["indicator"] == "Spare capacity"]
    if spare:
        alerts.append({"level": "Info", "text": f"{len(spare)} facility/facilities show spare configured capacity."})
    return alerts


# ---------------------------------------------------------------------------
# Dataframes for charts and tables
# ---------------------------------------------------------------------------
def _ids(state, district, mandal, category, active):
    return None  # placeholder kept for readability


def facility_type_df(session: Session, ids: list[int]) -> pd.DataFrame:
    return pd.DataFrame(facility_service.facility_count_by_type(session, facility_ids=ids))


def screening_by_month_df(session: Session, ids: list[int]) -> pd.DataFrame:
    if not ids:
        return pd.DataFrame(columns=["month", "screenings"])
    rows = session.execute(
        select(ScreeningEvent.event_date)
        .join(Screening, Screening.event_id == ScreeningEvent.id)
        .where(ScreeningEvent.facility_id.in_(ids))
    ).scalars().all()
    if not rows:
        return pd.DataFrame(columns=["month", "screenings"])
    frame = pd.DataFrame({"date": pd.to_datetime(rows)})
    frame["month"] = frame["date"].dt.strftime("%b %Y")
    counts = frame.groupby("month").size().reset_index(name="screenings")
    counts["_sort"] = pd.to_datetime(counts["month"], format="%b %Y")
    return counts.sort_values("_sort").drop(columns="_sort").tail(8)


def referral_status_df(session: Session, ids: list[int]) -> pd.DataFrame:
    if not ids:
        return pd.DataFrame(columns=["status", "count"])
    rows = session.execute(
        select(Referral.status, func.count(Referral.id))
        .where(Referral.source_facility_id.in_(ids))
        .group_by(Referral.status)
    ).all()
    return pd.DataFrame([{"status": s, "count": c} for s, c in rows]) if rows else pd.DataFrame(columns=["status", "count"])


def utilization_df(session: Session, ids: list[int]) -> pd.DataFrame:
    return pd.DataFrame(facility_service.utilization_rows(session, facility_ids=ids))


def staffing_gap_df(session: Session, ids: list[int]) -> pd.DataFrame:
    if not ids:
        return pd.DataFrame(columns=["facility", "role", "required", "filled", "gap", "priority"])
    rows = session.execute(
        select(Facility.name, StaffVacancy.role, StaffVacancy.required_count,
               StaffVacancy.filled_count, StaffVacancy.priority)
        .join(Facility, Facility.id == StaffVacancy.facility_id)
        .where(StaffVacancy.facility_id.in_(ids))
        .order_by((StaffVacancy.required_count - StaffVacancy.filled_count).desc())
    ).all()
    data = [
        {"facility": f, "role": r, "required": req, "filled": fill, "gap": max(req - fill, 0), "priority": p}
        for f, r, req, fill, p in rows if req - fill > 0
    ]
    return pd.DataFrame(data, columns=["facility", "role", "required", "filled", "gap", "priority"])


def service_demand_df(session: Session, ids: list[int]) -> pd.DataFrame:
    if not ids:
        return pd.DataFrame(columns=["screening_type", "observations"])
    rows = session.execute(
        select(Screening.screening_type, func.count(Screening.id))
        .join(ScreeningEvent, ScreeningEvent.id == Screening.event_id)
        .where(ScreeningEvent.facility_id.in_(ids))
        .group_by(Screening.screening_type)
        .order_by(func.count(Screening.id).desc())
    ).all()
    return pd.DataFrame([{"screening_type": t, "observations": c} for t, c in rows])


def service_availability_df(session: Session, ids: list[int]) -> pd.DataFrame:
    return pd.DataFrame(
        facility_service.service_availability_matrix(session, facility_ids=ids),
        columns=["service", "facilities"],
    )


def facilities_df(session: Session, ids: list[int] | None = None) -> pd.DataFrame:
    scoped = _facilities(session, ids) if ids is not None else facility_service.search_facilities(session)
    return pd.DataFrame([
        {
            "code": f.code, "name": f.name, "type": f.type,
            "category": facility_service.category_of(f),
            "state": f.state, "district": f.district, "mandal": f.mandal,
            "locality": f.locality, "ownership": f.ownership,
            "beds": f.beds, "catchment_population": f.catchment_population,
            "verification": f.verification_status, "operating": f.operating_status,
            "active": "Active" if f.is_active else "Inactive",
            "services": ", ".join(s.service_name for s in f.services),
            "capacity_notes": f.capacity_notes,
        }
        for f in scoped
    ])


def screenings_df(session: Session, ids: list[int] | None = None) -> pd.DataFrame:
    from src.models import Participant

    stmt = (
        select(Screening, Participant.synthetic_code, ScreeningEvent.event_name,
               Facility.name, ScreeningEvent.event_date)
        .join(Participant, Participant.id == Screening.participant_id)
        .join(ScreeningEvent, ScreeningEvent.id == Screening.event_id)
        .join(Facility, Facility.id == ScreeningEvent.facility_id)
        .order_by(Screening.created_at.desc())
    )
    if ids is not None:
        stmt = stmt.where(ScreeningEvent.facility_id.in_(ids))
    rows = session.execute(stmt).all()
    return pd.DataFrame([
        {
            "screening_id": s.id, "participant": code, "event": event,
            "facility": facility, "event_date": event_date.isoformat(),
            "screening_type": s.screening_type, "result_category": s.result_category,
            "review_status": s.review_status, "reviewed_by": s.reviewed_by or "",
        }
        for s, code, event, facility, event_date in rows
    ])


def referrals_df(session: Session, ids: list[int] | None = None) -> pd.DataFrame:
    from src.models import Participant

    stmt = (
        select(Referral, Participant.synthetic_code, Facility.name, Facility.id)
        .join(Participant, Participant.id == Referral.participant_id)
        .join(Facility, Facility.id == Referral.source_facility_id)
        .order_by(Referral.created_at.desc())
    )
    if ids is not None:
        stmt = stmt.where(Referral.source_facility_id.in_(ids))
    rows = session.execute(stmt).all()
    dest_names = dict(session.execute(select(Facility.id, Facility.name)).all())
    today = date.today()
    return pd.DataFrame([
        {
            "referral_code": r.referral_code, "participant": code,
            "source": src, "destination": dest_names.get(dest_id, ""),
            "reason": r.reason_category, "priority": r.priority, "status": r.status,
            "referring_doctor": r.referring_doctor,
            "follow_up_date": r.follow_up_date.isoformat() if r.follow_up_date else "",
            "overdue": bool(r.follow_up_date and r.follow_up_date < today
                            and r.status in {"Sent", "Accepted", "Scheduled", "Returned for clarification"}),
        }
        for r, code, src, dest_id in rows
    ])


def staff_df(session: Session, ids: list[int] | None = None) -> pd.DataFrame:
    facility_names = dict(session.execute(select(Facility.id, Facility.name)).all())
    stmt = select(Staff).order_by(Staff.role, Staff.display_name)
    if ids is not None:
        stmt = stmt.where(Staff.facility_id.in_(ids))
    staff = session.scalars(stmt).all()
    return pd.DataFrame([
        {
            "code": s.staff_code, "name": s.display_name, "role": s.role,
            "qualification": s.qualification,
            "facility": facility_names.get(s.facility_id, "Unassigned"),
            "skills": s.skills, "availability": s.availability, "shift": s.shift,
            "employment_type": s.employment_type, "verification": s.verification_status,
        }
        for s in staff
    ])


def vacancies_df(session: Session, ids: list[int] | None = None) -> pd.DataFrame:
    facility_names = dict(session.execute(select(Facility.id, Facility.name)).all())
    stmt = select(StaffVacancy).order_by(StaffVacancy.priority, StaffVacancy.role)
    if ids is not None:
        stmt = stmt.where(StaffVacancy.facility_id.in_(ids))
    rows = session.scalars(stmt).all()
    return pd.DataFrame([
        {
            "vacancy_code": v.vacancy_code,
            "facility": facility_names.get(v.facility_id, ""),
            "role": v.role, "required": v.required_count, "filled": v.filled_count,
            "gap": max(v.required_count - v.filled_count, 0),
            "status": v.status, "priority": v.priority, "notes": v.notes,
        }
        for v in rows
    ])


def applications_df(session: Session, ids: list[int] | None = None) -> pd.DataFrame:
    facility_names = dict(session.execute(select(Facility.id, Facility.name)).all())
    stmt = select(EmploymentApplication).order_by(EmploymentApplication.applied_at.desc())
    if ids is not None:
        stmt = stmt.where(EmploymentApplication.facility_id.in_(ids))
    rows = session.scalars(stmt).all()
    return pd.DataFrame([
        {
            "application_code": a.application_code, "applicant": a.applicant_alias,
            "role": a.role, "facility": facility_names.get(a.facility_id, ""),
            "qualification": a.qualification, "experience_years": a.experience_years,
            "status": a.status, "applied_at": a.applied_at.strftime("%Y-%m-%d"),
        }
        for a in rows
    ])


def campaigns_df(session: Session) -> pd.DataFrame:
    rows = session.scalars(select(Campaign).order_by(Campaign.schedule_at)).all()
    return pd.DataFrame([
        {
            "title": c.title, "language": c.language, "audience": c.audience,
            "target_area": c.target_area, "channel": c.planned_channel,
            "schedule": c.schedule_at.strftime("%Y-%m-%d %H:%M"),
            "status": c.status, "delivery": c.delivery_status,
        }
        for c in rows
    ])


def notifications_df(session: Session) -> pd.DataFrame:
    rows = session.scalars(select(Notification).order_by(Notification.schedule_at.desc())).all()
    return pd.DataFrame([
        {
            "title": n.title, "audience": n.audience, "channel": n.channel,
            "status": n.status, "related_entity": n.related_entity,
            "schedule": n.schedule_at.strftime("%Y-%m-%d %H:%M"),
            "message": n.message,
        }
        for n in rows
    ])


def substance_df(session: Session) -> pd.DataFrame:
    from src.models import Participant

    rows = session.execute(
        select(SubstanceUseCase, Participant.synthetic_code)
        .join(Participant, Participant.id == SubstanceUseCase.participant_id)
        .order_by(SubstanceUseCase.updated_at.desc())
    ).all()
    return pd.DataFrame([
        {
            "case_code": c.case_code, "participant": code,
            "substance_category": c.substance_category,
            "consent": c.consent_status,
            "confidentiality": c.confidentiality_level,
            "counselling_status": c.counselling_status,
            "assigned_counsellor": c.assigned_counsellor,
            "follow_up_date": c.follow_up_date.strftime("%Y-%m-%d") if c.follow_up_date else "",
        }
        for c, code in rows
    ])


def appointments_df(session: Session, participant_id: int | None = None) -> pd.DataFrame:
    from src.models import Participant

    stmt = (
        select(Appointment, Participant.synthetic_code, Facility.name)
        .join(Participant, Participant.id == Appointment.participant_id)
        .join(Facility, Facility.id == Appointment.facility_id)
        .order_by(Appointment.preferred_date.desc())
    )
    if participant_id is not None:
        stmt = stmt.where(Appointment.participant_id == participant_id)
    rows = session.execute(stmt).all()
    return pd.DataFrame([
        {
            "appointment_code": a.appointment_code, "participant": code,
            "facility": facility, "service": a.service_name,
            "preferred_date": a.preferred_date.strftime("%Y-%m-%d %H:%M"),
            "status": a.status, "contact_preference": a.contact_preference,
        }
        for a, code, facility in rows
    ])


# ---------------------------------------------------------------------------
# Exports and reports
# ---------------------------------------------------------------------------
def export_csv(session: Session, kind: str, ids: list[int] | None = None) -> str:
    frames = {
        "Facilities": lambda: facilities_df(session, ids),
        "Service utilisation": lambda: utilization_df(session, ids if ids is not None else scope_ids(session)),
        "Staffing gaps": lambda: staffing_gap_df(session, ids if ids is not None else scope_ids(session)),
        "Workforce": lambda: staff_df(session, ids),
        "Screenings": lambda: screenings_df(session, ids),
        "Referrals": lambda: referrals_df(session, ids),
        "Diagnostics": lambda: diagnostics_df(session, ids),
        "Campaigns": lambda: campaigns_df(session),
        "Notifications": lambda: notifications_df(session),
        "Substance-use cases": lambda: substance_df(session),
        "Employment applications": lambda: applications_df(session, ids),
        "Appointments": lambda: appointments_df(session),
    }
    if kind not in frames:
        raise ValueError(f"Unknown export type: {kind}")
    frame = frames[kind]()
    if frame.empty:
        return ""
    return frame.to_csv(index=False)


def diagnostics_df(session: Session, ids: list[int] | None = None) -> pd.DataFrame:
    stmt = (
        select(LabOrder, Referral.referral_code, Facility.name)
        .join(Referral, Referral.id == LabOrder.referral_id)
        .join(Facility, Facility.id == LabOrder.lab_facility_id)
        .order_by(LabOrder.updated_at.desc())
    )
    if ids is not None:
        stmt = stmt.where(LabOrder.lab_facility_id.in_(ids))
    rows = session.execute(stmt).all()
    return pd.DataFrame([
        {
            "order_code": o.order_code, "referral": ref, "lab": lab,
            "test_category": o.test_category, "priority": o.priority,
            "sample_status": o.sample_status, "report_status": o.report_status,
            "reviewer_status": o.reviewer_status,
            "updated_at": o.updated_at.strftime("%Y-%m-%d %H:%M"),
        }
        for o, ref, lab in rows
    ])


def reports_summary(session: Session, ids: list[int] | None = None) -> dict[str, object]:
    if ids is None:
        kpis = overview_kpis(session)
    else:
        facility = session.get(Facility, ids[0]) if ids else None
        district = facility.district if facility else "All"
        kpis = overview_kpis(session, district=district)
    util = facility_service.utilization_rows(session, facility_ids=ids)
    active_util = [r for r in util if r["configured_capacity"] > 0 and r["completed_sessions"] > 0]
    avg_util = round(sum(r["utilization_pct"] for r in active_util) / len(active_util), 1) if active_util else 0.0
    return {
        **kpis,
        "avg_utilization_pct": avg_util,
        "today": date.today().isoformat(),
    }


def scope_label(state: str, district: str, mandal: str, category: str, active: str) -> str:
    parts = []
    for label, value in (("State", state), ("District", district), ("Mandal", mandal),
                         ("Category", category), ("Status", active)):
        if value and value != "All":
            parts.append(f"{label}: {value}")
    return " · ".join(parts) if parts else "All demo geographies"


def referral_transition_options(status: str) -> list[str]:
    return sorted(REFERRAL_TRANSITIONS.get(status, set()))
