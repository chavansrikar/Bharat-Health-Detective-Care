"""Referral coordination with enforced status transitions and safety rules."""
from __future__ import annotations

from datetime import date

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from src.config import REFERRAL_TRANSITIONS
from src.models import Facility, Participant, Referral, Screening, Service
from src.models.base import utcnow

OPEN_STATUSES = {"Draft", "Sent", "Accepted", "Scheduled", "Returned for clarification"}

EMERGENCY_CAPABLE_TYPES = {
    "CHC",
    "District Hospital",
    "Medical College Hospital",
    "Private Hospital / Lab (participating)",
}


def create_referral(
    session: Session,
    participant_id: int,
    source_facility_id: int,
    destination_facility_id: int,
    reason_category: str,
    priority: str = "Routine",
    screening_id: int | None = None,
    follow_up_date: date | None = None,
    created_by: str = "Demo user",
    referring_doctor: str = "Demo clinician",
) -> Referral:
    if session.get(Participant, participant_id) is None:
        raise ValueError("Choose a valid participant")
    source = session.get(Facility, source_facility_id)
    destination = session.get(Facility, destination_facility_id)
    if source is None or destination is None:
        raise ValueError("Choose valid source and destination facilities")
    if not reason_category.strip():
        raise ValueError("Referral reason is required")
    if priority not in {"Routine", "Urgent"}:
        raise ValueError("Priority must be Routine or Urgent")
    if priority == "Urgent":
        has_emergency = destination.type in EMERGENCY_CAPABLE_TYPES or bool(
            session.scalar(
                select(Service.id).where(
                    Service.facility_id == destination.id,
                    Service.service_name == "Emergency care",
                    Service.active.is_(True),
                )
            )
        )
        if not has_emergency:
            raise ValueError(
                "Safety rule: urgent referrals must go to a facility with emergency capability. "
                "Do not divert urgent symptoms to a lower-level facility."
            )
    count = int(session.scalar(select(func.count()).select_from(Referral)) or 0)
    referral = Referral(
        referral_code=f"REF-{count + 1:04d}", participant_id=participant_id,
        screening_id=screening_id, source_facility_id=source_facility_id,
        destination_facility_id=destination_facility_id,
        reason_category=reason_category.strip(), priority=priority,
        status="Draft", created_by=created_by, follow_up_date=follow_up_date,
        referring_doctor=referring_doctor.strip() or "Demo clinician",
    )
    session.add(referral)
    session.flush()
    return referral


def transition_referral(session: Session, referral_id: int, new_status: str, closure_note: str = "") -> Referral:
    referral = session.get(Referral, referral_id)
    if referral is None:
        raise ValueError("Referral not found")
    allowed = REFERRAL_TRANSITIONS.get(referral.status, set())
    if new_status not in allowed:
        raise ValueError(
            f"Invalid transition: {referral.status} → {new_status}. Allowed: {', '.join(sorted(allowed)) or 'none'}"
        )
    referral.status = new_status
    if new_status == "Completed":
        referral.closed_at = utcnow()
        referral.closure_note = closure_note
    session.flush()
    return referral


def list_referrals(
    session: Session,
    status: str = "All",
    priority: str = "All",
    overdue_only: bool = False,
    facility_ids: list[int] | None = None,
) -> list[dict]:
    stmt = (
        select(
            Referral, Participant.synthetic_code,
            Facility.name, Referral.destination_facility_id,
        )
        .join(Participant, Participant.id == Referral.participant_id)
        .join(Facility, Facility.id == Referral.source_facility_id)
        .order_by(Referral.created_at.desc())
    )
    if status and status != "All":
        stmt = stmt.where(Referral.status == status)
    if priority and priority != "All":
        stmt = stmt.where(Referral.priority == priority)
    if facility_ids is not None:
        stmt = stmt.where(Referral.source_facility_id.in_(facility_ids))
    rows = session.execute(stmt).all()
    dest_names = dict(session.execute(select(Facility.id, Facility.name)).all())
    today = date.today()
    out = []
    for ref, participant, source_name, dest_id in rows:
        is_overdue = bool(
            ref.follow_up_date
            and ref.follow_up_date < today
            and ref.status in {"Sent", "Accepted", "Scheduled", "Returned for clarification"}
        )
        if overdue_only and not is_overdue:
            continue
        out.append(
            {
                "referral_id": ref.id,
                "referral_code": ref.referral_code,
                "participant": participant,
                "source": source_name,
                "destination": dest_names.get(dest_id, ""),
                "reason": ref.reason_category,
                "priority": ref.priority,
                "status": ref.status,
                "follow_up_date": ref.follow_up_date.isoformat() if ref.follow_up_date else "",
                "overdue": is_overdue,
                "referring_doctor": ref.referring_doctor,
                "created_by": ref.created_by,
            }
        )
    return out


def overdue_count(session: Session) -> int:
    return sum(1 for row in list_referrals(session) if row["overdue"])


def open_count(session: Session) -> int:
    return int(
        session.scalar(select(func.count()).select_from(Referral).where(Referral.status.in_(OPEN_STATUSES))) or 0
    )


def referral_status_distribution(session: Session) -> list[dict]:
    rows = session.execute(
        select(Referral.status, func.count(Referral.id)).group_by(Referral.status)
    ).all()
    return [{"status": status, "count": count} for status, count in rows]
