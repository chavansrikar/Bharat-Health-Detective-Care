"""Diagnostic laboratory workflow (status-only demo, no clinical values)."""
from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from src.config import LAB_FLOW
from src.models import Facility, LabOrder, Participant, Referral
from src.models.base import utcnow


def list_orders(session: Session, facility_ids: list[int] | None = None, status: str = "All") -> list[dict]:
    stmt = (
        select(LabOrder, Referral.referral_code, Facility.name)
        .join(Referral, Referral.id == LabOrder.referral_id)
        .join(Facility, Facility.id == LabOrder.lab_facility_id)
        .order_by(LabOrder.updated_at.desc())
    )
    if facility_ids is not None:
        stmt = stmt.where(LabOrder.lab_facility_id.in_(facility_ids))
    rows = session.execute(stmt).all()
    out = [
        {
            "order_id": order.id,
            "order_code": order.order_code,
            "referral": ref_code,
            "lab": lab_name,
            "test_category": order.test_category,
            "priority": order.priority,
            "requested_by": order.requested_by,
            "sample_status": order.sample_status,
            "result_status": order.result_status,
            "report_status": order.report_status,
            "reviewer_status": order.reviewer_status,
            "demo_note": order.demo_result_note,
            "updated_at": order.updated_at.strftime("%Y-%m-%d %H:%M"),
        }
        for order, ref_code, lab_name in rows
    ]
    if status and status != "All":
        out = [row for row in out if row["report_status"] == status]
    return out


def order_choices(session: Session) -> list[tuple[str, int]]:
    return [(o["order_code"] + " — " + o["test_category"], o["order_id"]) for o in list_orders(session)]


def next_status(current: str) -> str | None:
    try:
        idx = LAB_FLOW.index(current)
    except ValueError:
        return None
    return LAB_FLOW[idx + 1] if idx + 1 < len(LAB_FLOW) else None


def advance_order(session: Session, order_id: int) -> LabOrder:
    order = session.get(LabOrder, order_id)
    if order is None:
        raise ValueError("Lab order not found")
    expected = next_status(order.sample_status)
    if expected is None:
        raise ValueError("This order is already at the final workflow stage")
    order.sample_status = expected
    if expected == "Result available":
        order.result_status = "Result available"
        order.reviewer_status = "Awaiting clinician review"
        order.report_status = "Result entered"
        order.demo_result_note = "Demo status only — clinician confirmation required"
    elif expected == "Clinician reviewed":
        order.result_status = "Reviewed"
        order.reviewer_status = "Reviewed by clinician"
        order.report_status = "Verified"
    order.updated_at = utcnow()
    session.flush()
    return order


def enter_result(session: Session, order_id: int) -> LabOrder:
    order = session.get(LabOrder, order_id)
    if order is None:
        raise ValueError("Lab order not found")
    order.sample_status = "Result available"
    order.result_status = "Result available"
    order.report_status = "Result entered"
    order.reviewer_status = "Awaiting clinician review"
    order.demo_result_note = "Demo status only — clinician confirmation required"
    order.updated_at = utcnow()
    session.flush()
    return order


def mark_result_available(session: Session, order_id: int) -> LabOrder:
    return enter_result(session, order_id)


def verify_report(session: Session, order_id: int) -> LabOrder:
    order = session.get(LabOrder, order_id)
    if order is None:
        raise ValueError("Lab order not found")
    if order.result_status != "Result available":
        raise ValueError("A result must be available before clinician review")
    order.sample_status = "Clinician reviewed"
    order.result_status = "Reviewed"
    order.reviewer_status = "Reviewed by clinician"
    order.report_status = "Verified"
    order.updated_at = utcnow()
    session.flush()
    return order


def mark_reviewed(session: Session, order_id: int) -> LabOrder:
    return verify_report(session, order_id)


def deliver_report(session: Session, order_id: int) -> LabOrder:
    order = session.get(LabOrder, order_id)
    if order is None:
        raise ValueError("Lab order not found")
    if order.report_status != "Verified":
        raise ValueError("Only a verified report can be marked as delivered")
    order.report_status = "Delivered"
    order.updated_at = utcnow()
    session.flush()
    return order


def awaiting_review_count(session: Session) -> int:
    return int(
        session.scalar(
            select(func.count()).select_from(LabOrder).where(LabOrder.reviewer_status == "Awaiting clinician review")
        )
        or 0
    )


def pending_report_count(session: Session) -> int:
    return int(
        session.scalar(
            select(func.count()).select_from(LabOrder).where(LabOrder.report_status != "Delivered")
        )
        or 0
    )


def report_status_distribution(session: Session) -> list[dict]:
    rows = session.execute(
        select(LabOrder.report_status, func.count(LabOrder.id)).group_by(LabOrder.report_status)
    ).all()
    return [{"status": status, "count": count} for status, count in rows]


def orders_for_participant(session: Session, participant_id: int) -> list[dict]:
    rows = session.execute(
        select(LabOrder, Referral.referral_code)
        .join(Referral, Referral.id == LabOrder.referral_id)
        .where(Referral.participant_id == participant_id)
    ).all()
    return [
        {
            "order_code": order.order_code, "test": order.test_category,
            "report_status": order.report_status, "status": order.reviewer_status,
        }
        for order, code in rows
    ]
