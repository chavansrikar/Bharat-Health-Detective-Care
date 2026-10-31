"""Voluntary, confidential substance-use prevention and counselling support.

Design rules enforced here: participation requires recorded consent, cases are
restricted to the counselling team, and no punitive or enforcement workflow is
provided. This module records support, not criminal or employment action.
"""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from src.config import SUBSTANCE_STATUSES
from src.models import Participant, SubstanceUseCase
from src.models.base import utcnow

CONFIDENTIALITY = "Restricted — counselling team only"


def list_cases(session: Session, status: str = "All", text: str = "") -> list[dict]:
    stmt = (
        select(SubstanceUseCase, Participant.synthetic_code, Participant.display_name_alias)
        .join(Participant, Participant.id == SubstanceUseCase.participant_id)
        .order_by(SubstanceUseCase.updated_at.desc())
    )
    if status and status != "All":
        stmt = stmt.where(SubstanceUseCase.counselling_status == status)
    if text:
        like = f"%{text.strip().lower()}%"
        stmt = stmt.where(
            func.lower(SubstanceUseCase.case_code).like(like)
            | func.lower(SubstanceUseCase.substance_category).like(like)
            | func.lower(Participant.synthetic_code).like(like)
        )
    rows = session.execute(stmt).all()
    return [
        {
            "case_id": c.id, "case_code": c.case_code,
            "participant": code, "participant_alias": alias,
            "substance_category": c.substance_category,
            "screening_note": c.screening_note,
            "consent": c.consent_status,
            "confidentiality": c.confidentiality_level,
            "counselling_status": c.counselling_status,
            "assigned_counsellor": c.assigned_counsellor,
            "follow_up_date": c.follow_up_date.strftime("%Y-%m-%d") if c.follow_up_date else "",
        }
        for c, code, alias in rows
    ]


def case_choices(session: Session) -> list[tuple[str, int]]:
    return [(c["case_code"] + " — " + c["participant"], c["case_id"]) for c in list_cases(session)]


def create_case(
    session: Session,
    participant_id: int,
    substance_category: str,
    screening_note: str = "",
    consent_status: str = "Granted (demo)",
    assigned_counsellor: str = "Unassigned",
    follow_up_date: datetime | None = None,
) -> SubstanceUseCase:
    if session.get(Participant, participant_id) is None:
        raise ValueError("Choose a valid participant")
    if not substance_category.strip():
        raise ValueError("Substance category is required")
    if not consent_status.startswith("Granted"):
        raise ValueError(
            "Consent is required for voluntary support. A case cannot be created without recorded consent."
        )
    count = int(session.scalar(select(func.count()).select_from(SubstanceUseCase)) or 0)
    case = SubstanceUseCase(
        case_code=f"SU-{count + 1:04d}", participant_id=participant_id,
        substance_category=substance_category.strip(), screening_note=screening_note.strip(),
        consent_status=consent_status, confidentiality_level=CONFIDENTIALITY,
        counselling_status="Screening recorded", assigned_counsellor=assigned_counsellor,
        follow_up_date=follow_up_date,
    )
    session.add(case)
    session.flush()
    return case


def update_case(
    session: Session,
    case_id: int,
    status: str | None = None,
    counsellor: str | None = None,
    note: str | None = None,
) -> SubstanceUseCase:
    case = session.get(SubstanceUseCase, case_id)
    if case is None:
        raise ValueError("Substance-use case not found")
    if status is not None:
        if status not in SUBSTANCE_STATUSES:
            raise ValueError("Invalid counselling status")
        case.counselling_status = status
    if counsellor is not None and counsellor.strip():
        case.assigned_counsellor = counsellor.strip()
    if note is not None:
        case.screening_note = note.strip()
    case.updated_at = utcnow()
    session.flush()
    return case


def summary(session: Session) -> dict[str, int]:
    cases = session.scalars(select(SubstanceUseCase)).all()
    return {
        "cases": len(cases),
        "consented": sum(1 for c in cases if c.consent_status.startswith("Granted")),
        "scheduled": sum(1 for c in cases if c.counselling_status == "Counselling scheduled"),
        "completed": sum(1 for c in cases if c.counselling_status == "Counselling completed"),
        "referred": sum(1 for c in cases if c.counselling_status == "Referred"),
        "closed": sum(1 for c in cases if c.counselling_status == "Closed"),
    }


def substance_distribution(session: Session) -> list[dict]:
    rows = session.execute(
        select(SubstanceUseCase.substance_category, func.count(SubstanceUseCase.id))
        .group_by(SubstanceUseCase.substance_category)
        .order_by(func.count(SubstanceUseCase.id).desc())
    ).all()
    return [{"substance_category": category, "cases": count} for category, count in rows]


def cases_for_participant(session: Session, participant_id: int) -> list[dict]:
    rows = session.scalars(
        select(SubstanceUseCase).where(SubstanceUseCase.participant_id == participant_id)
    ).all()
    return [
        {
            "case_code": c.case_code, "substance_category": c.substance_category,
            "counselling_status": c.counselling_status,
            "assigned_counsellor": c.assigned_counsellor,
            "follow_up_date": c.follow_up_date.strftime("%Y-%m-%d") if c.follow_up_date else "",
        }
        for c in rows
    ]
