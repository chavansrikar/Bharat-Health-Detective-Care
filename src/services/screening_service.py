"""Preventive programmes, screening events and clinician review."""
from __future__ import annotations

from datetime import date

from sqlalchemy import case, func, select
from sqlalchemy.orm import Session

from src.models import Participant, Programme, Screening, ScreeningEvent


def list_programmes(session: Session) -> list[Programme]:
    return list(session.scalars(select(Programme).order_by(Programme.name)).all())


def programme_choices(session: Session) -> list[tuple[str, int]]:
    return [(p.name, p.id) for p in list_programmes(session)]


def create_programme(
    session: Session,
    name: str,
    description: str,
    cohort_text: str,
    eligibility_notes: str,
    start_date: date,
    end_date: date,
    status: str = "Active",
) -> Programme:
    if not name.strip():
        raise ValueError("Programme name is required")
    if end_date < start_date:
        raise ValueError("End date cannot be before start date")
    programme = Programme(
        name=name.strip(), description=description.strip(), cohort_text=cohort_text.strip(),
        eligibility_notes=eligibility_notes.strip(),
        guidance_reference="Confirm with local clinical authority",
        start_date=start_date, end_date=end_date, status=status,
    )
    session.add(programme)
    session.flush()
    return programme


def facility_event_choices(session: Session, facility_ids: list[int] | None = None) -> list[tuple[str, int]]:
    stmt = select(ScreeningEvent.event_name, ScreeningEvent.id).order_by(ScreeningEvent.event_date.desc())
    if facility_ids is not None:
        stmt = stmt.where(ScreeningEvent.facility_id.in_(facility_ids))
    rows = session.execute(stmt).all()
    return [(name, eid) for name, eid in rows]


def create_event(
    session: Session,
    programme_id: int,
    facility_id: int,
    event_name: str,
    event_date: date,
    status: str = "Planned",
) -> ScreeningEvent:
    if not event_name.strip():
        raise ValueError("Event name is required")
    if session.get(Programme, programme_id) is None:
        raise ValueError("Choose a valid programme")
    count = int(session.scalar(select(func.count()).select_from(ScreeningEvent)) or 0)
    event = ScreeningEvent(
        event_code=f"EV-{count + 1:03d}", programme_id=programme_id,
        facility_id=facility_id, event_name=event_name.strip(),
        event_date=event_date, status=status,
    )
    session.add(event)
    session.flush()
    return event


def list_events(session: Session, facility_ids: list[int] | None = None) -> list[dict]:
    stmt = (
        select(ScreeningEvent, Programme.name, func.count(Screening.id))
        .join(Programme, Programme.id == ScreeningEvent.programme_id)
        .outerjoin(Screening, Screening.event_id == ScreeningEvent.id)
        .group_by(ScreeningEvent.id)
        .order_by(ScreeningEvent.event_date.desc())
    )
    if facility_ids is not None:
        stmt = stmt.where(ScreeningEvent.facility_id.in_(facility_ids))
    rows = session.execute(stmt).all()
    return [
        {
            "event_id": ev.id,
            "event_code": ev.event_code,
            "event_name": ev.event_name,
            "programme": prog,
            "event_date": ev.event_date.isoformat(),
            "status": ev.status,
            "screenings": count,
        }
        for ev, prog, count in rows
    ]


def participant_choices(session: Session) -> list[tuple[str, int]]:
    rows = session.execute(
        select(Participant.synthetic_code, Participant.display_name_alias, Participant.id).order_by(Participant.synthetic_code)
    ).all()
    return [(f"{code} — {alias}", pid) for code, alias, pid in rows]


def register_participant(
    session: Session,
    alias: str,
    age_band: str,
    locality: str,
    consent_status: str = "Granted (demo)",
    assigned_worker: str = "Unassigned",
) -> Participant:
    if not alias.strip():
        raise ValueError("Participant alias is required")
    count = int(session.scalar(select(func.count()).select_from(Participant)) or 0)
    participant = Participant(
        synthetic_code=f"P-{count + 1:04d}", display_name_alias=alias.strip(),
        age_band=age_band, locality=locality.strip() or "Unspecified",
        consent_status=consent_status, assigned_worker=assigned_worker,
    )
    session.add(participant)
    session.flush()
    return participant


def record_screening(
    session: Session,
    participant_id: int,
    event_id: int,
    screening_type: str,
    observation_text: str,
    result_category: str,
) -> Screening:
    if not screening_type.strip():
        raise ValueError("Screening type is required")
    if session.get(Participant, participant_id) is None:
        raise ValueError("Choose a valid participant")
    if session.get(ScreeningEvent, event_id) is None:
        raise ValueError("Choose a valid screening event")
    if result_category not in {"Normal", "Needs clinician review", "Urgent review"}:
        raise ValueError("Invalid result category")
    screening = Screening(
        participant_id=participant_id, event_id=event_id,
        screening_type=screening_type.strip(), observation_text=observation_text.strip(),
        result_category=result_category, review_status="Pending clinician review",
    )
    session.add(screening)
    session.flush()
    return screening


def review_queue(session: Session) -> list[dict]:
    rows = session.execute(
        select(Screening, Participant.synthetic_code, Participant.display_name_alias, ScreeningEvent.event_name)
        .join(Participant, Participant.id == Screening.participant_id)
        .join(ScreeningEvent, ScreeningEvent.id == Screening.event_id)
        .where(Screening.review_status == "Pending clinician review")
        .order_by(
            case((Screening.result_category == "Urgent review", 0), else_=1),
            Screening.created_at.desc(),
        )
    ).all()
    return [
        {
            "screening_id": s.id,
            "participant": f"{code} — {alias}",
            "event": event,
            "screening_type": s.screening_type,
            "result_category": s.result_category,
            "review_status": s.review_status,
            "observation": s.observation_text,
        }
        for s, code, alias, event in rows
    ]


def all_screenings(session: Session) -> list[dict]:
    rows = session.execute(
        select(Screening, Participant.synthetic_code, ScreeningEvent.event_name)
        .join(Participant, Participant.id == Screening.participant_id)
        .join(ScreeningEvent, ScreeningEvent.id == Screening.event_id)
        .order_by(Screening.created_at.desc())
    ).all()
    return [
        {
            "screening_id": s.id,
            "participant": code,
            "event": event,
            "screening_type": s.screening_type,
            "result_category": s.result_category,
            "review_status": s.review_status,
            "reviewed_by": s.reviewed_by or "",
        }
        for s, code, event in rows
    ]


def review_screening(session: Session, screening_id: int, reviewer: str, outcome: str = "Reviewed") -> Screening:
    screening = session.get(Screening, screening_id)
    if screening is None:
        raise ValueError("Screening record not found")
    if screening.review_status == "Reviewed":
        raise ValueError("This screening has already been reviewed")
    screening.review_status = outcome
    screening.reviewed_by = reviewer
    session.flush()
    return screening


def pending_review_count(session: Session) -> int:
    return int(
        session.scalar(
            select(func.count()).select_from(Screening).where(Screening.review_status == "Pending clinician review")
        )
        or 0
    )
