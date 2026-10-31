"""Citizen portal: registry self-registration, reminders, appointments, records."""
from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from src.config import APPOINTMENT_STATUSES
from src.models import (
    Appointment,
    Campaign,
    Facility,
    LabOrder,
    Notification,
    Participant,
    Referral,
    Screening,
    ScreeningEvent,
    Service,
    SubstanceUseCase,
)
from src.models.base import utcnow
from src.services import facility_service, screening_service


def participant_choices(session: Session) -> list[tuple[str, int]]:
    rows = session.execute(
        select(Participant.synthetic_code, Participant.display_name_alias, Participant.district, Participant.id)
        .order_by(Participant.synthetic_code)
    ).all()
    return [(f"{code} — {alias} ({district})", pid) for code, alias, district, pid in rows]


def get_participant(session: Session, participant_id: int) -> Participant | None:
    return session.get(Participant, participant_id)


def register_citizen(
    session: Session,
    alias: str,
    age_band: str,
    locality: str,
    gender: str = "Not recorded",
    district: str = "Yadadri Bhuvanagiri",
    consent_status: str = "Granted (demo)",
) -> Participant:
    if not consent_status.startswith("Granted"):
        raise ValueError("Consent is required to create a demo citizen profile.")
    participant = screening_service.register_participant(
        session, alias=alias, age_band=age_band, locality=locality, consent_status=consent_status
    )
    participant.gender = gender
    participant.district = district
    session.flush()
    return participant


def citizen_profile(session: Session, participant_id: int) -> dict:
    participant = session.get(Participant, participant_id)
    if participant is None:
        raise ValueError("Citizen record not found")
    return {
        "code": participant.synthetic_code,
        "alias": participant.display_name_alias,
        "age_band": participant.age_band,
        "gender": participant.gender,
        "locality": participant.locality,
        "district": participant.district,
        "consent": participant.consent_status,
        "assigned_worker": participant.assigned_worker,
    }


def _upcoming_reminders(session: Session, participant_id: int) -> list[str]:
    today = date.today()
    reminders: list[str] = []
    appointments = session.scalars(
        select(Appointment).where(
            Appointment.participant_id == participant_id,
            Appointment.status.in_(["Requested", "Confirmed"]),
        )
    ).all()
    for appointment in appointments:
        when = appointment.preferred_date.strftime("%d %b %Y, %H:%M")
        reminders.append(
            f"Appointment {appointment.appointment_code} for {appointment.service_name} on {when} "
            f"({appointment.status}). Confirm with the facility before travelling."
        )

    referrals = session.scalars(
        select(Referral).where(
            Referral.participant_id == participant_id,
            Referral.status.in_(["Sent", "Accepted", "Scheduled", "Returned for clarification"]),
        )
    ).all()
    for referral in referrals:
        due = referral.follow_up_date.strftime("%d %b %Y") if referral.follow_up_date else "date to confirm"
        overdue = " — follow-up date has passed" if referral.follow_up_date and referral.follow_up_date < today else ""
        reminders.append(
            f"Referral {referral.referral_code} is {referral.status.lower()}; next follow-up: {due}{overdue}. "
            "Contact the destination facility to confirm."
        )

    pending_labs = session.execute(
        select(LabOrder)
        .join(Referral, Referral.id == LabOrder.referral_id)
        .where(Referral.participant_id == participant_id, LabOrder.report_status != "Delivered")
    ).scalars().all()
    for order in pending_labs:
        reminders.append(
            f"Laboratory order {order.order_code} ({order.test_category}) is at report stage "
            f"'{order.report_status}'. Results are shared only after clinician verification."
        )

    pending_screenings = session.execute(
        select(Screening)
        .where(Screening.participant_id == participant_id, Screening.review_status == "Pending clinician review")
    ).scalars().all()
    for screening in pending_screenings:
        reminders.append(
            f"Your {screening.screening_type.lower()} screening is awaiting clinician review. "
            "A screening observation is not a diagnosis."
        )

    substance_cases = session.scalars(
        select(SubstanceUseCase).where(
            SubstanceUseCase.participant_id == participant_id,
            SubstanceUseCase.counselling_status.in_(["Counselling scheduled", "Referred"]),
        )
    ).all()
    for case in substance_cases:
        when = case.follow_up_date.strftime("%d %b %Y") if case.follow_up_date else "to be confirmed"
        reminders.append(
            f"Confidential counselling follow-up ({case.case_code}) is planned for {when}. "
            "This support is voluntary and non-punitive."
        )
    return reminders


def reminders(session: Session, participant_id: int) -> list[str]:
    items = _upcoming_reminders(session, participant_id)
    if not items:
        return [
            "No pending demo reminders. Routine check-ups and screening can be booked through the listed facilities.",
            "Seek emergency care immediately for severe symptoms; this portal is not an emergency service.",
        ]
    return items


def health_records(session: Session, participant_id: int) -> list[dict]:
    rows = session.execute(
        select(Screening, ScreeningEvent.event_name, ScreeningEvent.event_date)
        .join(ScreeningEvent, ScreeningEvent.id == Screening.event_id)
        .where(Screening.participant_id == participant_id)
        .order_by(ScreeningEvent.event_date.desc())
    ).all()
    return [
        {
            "record_type": "Screening",
            "reference": f"SC-{s.id:04d}",
            "detail": f"{s.screening_type} at {event}",
            "date": event_date.isoformat(),
            "status": s.review_status,
            "safety_note": "Screening observation only — not a diagnosis.",
        }
        for s, event, event_date in rows
    ]


def referral_records(session: Session, participant_id: int) -> list[dict]:
    destination = dict(session.execute(select(Facility.id, Facility.name)).all())
    rows = session.scalars(
        select(Referral).where(Referral.participant_id == participant_id).order_by(Referral.created_at.desc())
    ).all()
    return [
        {
            "record_type": "Referral",
            "reference": r.referral_code,
            "detail": f"{r.reason_category} → {destination.get(r.destination_facility_id, 'facility')}",
            "date": r.created_at.strftime("%Y-%m-%d"),
            "status": r.status,
            "safety_note": "Urgent symptoms need emergency care, not referral tracking.",
        }
        for r in rows
    ]


def lab_records(session: Session, participant_id: int) -> list[dict]:
    rows = session.execute(
        select(LabOrder)
        .join(Referral, Referral.id == LabOrder.referral_id)
        .where(Referral.participant_id == participant_id)
        .order_by(LabOrder.updated_at.desc())
    ).scalars().all()
    return [
        {
            "record_type": "Diagnostics",
            "reference": order.order_code,
            "detail": order.test_category,
            "date": order.updated_at.strftime("%Y-%m-%d"),
            "status": order.report_status,
            "safety_note": "Status-only demo record. No clinical result value is shown.",
        }
        for order in rows
    ]


def all_records(session: Session, participant_id: int) -> list[dict]:
    return health_records(session, participant_id) + referral_records(session, participant_id) + lab_records(session, participant_id)


def facility_options(session: Session, district: str = "All", service: str = "All") -> list[dict]:
    facilities = facility_service.search_facilities(
        session, district=district, service=service, active="Active", operating="Operational"
    )
    return [
        {
            "facility_id": f.id, "name": f.name, "type": f.type,
            "district": f.district, "mandal": f.mandal, "locality": f.locality,
            "operating": f.operating_status, "services": ", ".join(s.service_name for s in f.services),
        }
        for f in facilities
    ]


def create_appointment(
    session: Session,
    participant_id: int,
    facility_id: int,
    service_name: str,
    preferred_date: datetime,
    contact_preference: str = "Demo callback",
    notes: str = "",
) -> Appointment:
    if session.get(Participant, participant_id) is None:
        raise ValueError("Choose a valid citizen profile")
    facility = session.get(Facility, facility_id)
    if facility is None or not facility.is_active:
        raise ValueError("Choose an active facility")
    if not service_name.strip():
        raise ValueError("Service is required")
    if preferred_date < datetime.now():
        raise ValueError("Choose a future date and time for the appointment request")
    count = int(session.scalar(select(func.count()).select_from(Appointment)) or 0)
    appointment = Appointment(
        appointment_code=f"APT-{count + 1:04d}", participant_id=participant_id,
        facility_id=facility_id, service_name=service_name.strip(),
        preferred_date=preferred_date, status="Requested",
        contact_preference=contact_preference, notes=notes.strip(),
    )
    session.add(appointment)
    session.flush()
    return appointment


def list_appointments(session: Session, participant_id: int | None = None) -> list[dict]:
    facility_names = dict(session.execute(select(Facility.id, Facility.name)).all())
    stmt = select(Appointment).order_by(Appointment.preferred_date.desc())
    if participant_id is not None:
        stmt = stmt.where(Appointment.participant_id == participant_id)
    rows = session.scalars(stmt).all()
    return [
        {
            "appointment_id": a.id, "appointment_code": a.appointment_code,
            "facility": facility_names.get(a.facility_id, ""),
            "service": a.service_name,
            "preferred_date": a.preferred_date.strftime("%Y-%m-%d %H:%M"),
            "status": a.status, "contact_preference": a.contact_preference,
        }
        for a in rows
    ]


def appointment_choices(session: Session, participant_id: int | None = None) -> list[tuple[str, int]]:
    return [(a["appointment_code"] + " — " + a["service"], a["appointment_id"]) for a in list_appointments(session, participant_id)]


def update_appointment(session: Session, appointment_id: int, status: str) -> Appointment:
    appointment = session.get(Appointment, appointment_id)
    if appointment is None:
        raise ValueError("Appointment not found")
    if status not in APPOINTMENT_STATUSES:
        raise ValueError("Invalid appointment status")
    appointment.status = status
    appointment.updated_at = utcnow()
    session.flush()
    return appointment


def cancel_appointment(session: Session, appointment_id: int) -> Appointment:
    return update_appointment(session, appointment_id, "Cancelled")


def awareness_feed(session: Session) -> list[dict]:
    campaigns = session.scalars(
        select(Campaign).where(Campaign.status.in_(["Approved draft", "Scheduled (simulated)"])).order_by(Campaign.schedule_at)
    ).all()
    return [
        {
            "title": c.title, "message": c.message, "language": c.language,
            "audience": c.audience, "area": c.target_area,
            "channel": c.planned_channel, "status": c.status,
        }
        for c in campaigns
    ]


def citizen_notifications(session: Session) -> list[dict]:
    rows = session.scalars(
        select(Notification).where(
            Notification.status.in_(["Approved", "Simulated — sent"]),
            Notification.audience.ilike("%citizen%"),
        ).order_by(Notification.schedule_at.desc())
    ).all()
    return [
        {"title": n.title, "message": n.message, "channel": n.channel, "status": n.status}
        for n in rows
    ]


def service_options_for_facility(session: Session, facility_id: int) -> list[str]:
    return list(session.scalars(
        select(Service.service_name).where(Service.facility_id == facility_id, Service.active.is_(True))
    ).all())


def citizen_summary(session: Session, participant_id: int) -> dict[str, int]:
    appointments = session.scalars(
        select(Appointment).where(Appointment.participant_id == participant_id)
    ).all()
    referrals = session.scalars(
        select(Referral).where(Referral.participant_id == participant_id)
    ).all()
    screenings = session.scalars(
        select(Screening).where(Screening.participant_id == participant_id)
    ).all()
    return {
        "appointments": len(appointments),
        "open_referrals": sum(1 for r in referrals if r.status not in {"Completed", "Cancelled"}),
        "screenings": len(screenings),
        "records": len(all_records(session, participant_id)),
    }
