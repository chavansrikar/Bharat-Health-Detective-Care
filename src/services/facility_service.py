"""Facility directory, infrastructure search and utilization logic."""
from __future__ import annotations

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from src.config import FACILITY_CATEGORY_MAP, FACILITY_TYPES
from src.models import Facility, Referral, Screening, ScreeningEvent, Service


def category_of(facility: Facility) -> str:
    return FACILITY_CATEGORY_MAP.get(facility.type, "Other")


def category_types(category: str) -> list[str]:
    return [t for t, c in FACILITY_CATEGORY_MAP.items() if c == category]


def _facility_query():
    return select(Facility).order_by(Facility.name)


def filtered_facility_ids(
    session: Session,
    state: str = "All",
    district: str = "All",
    mandal: str = "All",
    category: str = "All",
    active: str = "All",
) -> list[int]:
    stmt = select(Facility.id)
    if state and state != "All":
        stmt = stmt.where(Facility.state == state)
    if district and district != "All":
        stmt = stmt.where(Facility.district == district)
    if mandal and mandal != "All":
        stmt = stmt.where(Facility.mandal == mandal)
    if category and category != "All":
        types = category_types(category)
        stmt = stmt.where(Facility.type.in_(types)) if types else stmt.where(Facility.type == "__none__")
    if active == "Active":
        stmt = stmt.where(Facility.is_active.is_(True))
    elif active == "Inactive":
        stmt = stmt.where(Facility.is_active.is_(False))
    return list(session.scalars(stmt).all())


def search_facilities(
    session: Session,
    text: str = "",
    facility_type: str = "All",
    mandal: str = "All",
    service: str = "All",
    verification: str = "All",
    operating: str = "All",
    state: str = "All",
    district: str = "All",
    category: str = "All",
    active: str = "All",
) -> list[Facility]:
    stmt = _facility_query()
    if text:
        like = f"%{text.strip().lower()}%"
        stmt = stmt.where(
            or_(
                func.lower(Facility.name).like(like),
                func.lower(Facility.locality).like(like),
                func.lower(Facility.type).like(like),
                func.lower(Facility.district).like(like),
                func.lower(Facility.address_label).like(like),
            )
        )
    if facility_type and facility_type != "All":
        stmt = stmt.where(Facility.type == facility_type)
    if mandal and mandal != "All":
        stmt = stmt.where(Facility.mandal == mandal)
    if state and state != "All":
        stmt = stmt.where(Facility.state == state)
    if district and district != "All":
        stmt = stmt.where(Facility.district == district)
    if verification and verification != "All":
        stmt = stmt.where(Facility.verification_status == verification)
    if operating and operating != "All":
        stmt = stmt.where(Facility.operating_status == operating)
    if active == "Active":
        stmt = stmt.where(Facility.is_active.is_(True))
    elif active == "Inactive":
        stmt = stmt.where(Facility.is_active.is_(False))
    if category and category != "All":
        types = category_types(category)
        stmt = stmt.where(Facility.type.in_(types)) if types else stmt.where(Facility.type == "__none__")
    if service and service != "All":
        stmt = stmt.where(Facility.services.any(Service.service_name == service))
    return list(session.scalars(stmt).all())


def get_facility(session: Session, facility_id: int) -> Facility | None:
    return session.get(Facility, facility_id)


def facility_service_names(session: Session) -> list[str]:
    return list(
        session.scalars(
            select(Service.service_name).where(Service.active.is_(True)).distinct().order_by(Service.service_name)
        ).all()
    )


def facility_choices(session: Session) -> list[tuple[str, int]]:
    return [(f"{f.code} — {f.name}", f.id) for f in session.scalars(_facility_query()).all()]


def create_facility(session: Session, payload: dict) -> Facility:
    required = ["name", "type", "mandal", "locality"]
    missing = [key for key in required if not str(payload.get(key, "")).strip()]
    if missing:
        raise ValueError(f"Missing required fields: {', '.join(missing)}")
    count = int(session.scalar(select(func.count()).select_from(Facility)) or 0)
    facility = Facility(
        code=payload.get("code") or f"NEW-{count + 1:03d}",
        name=payload["name"].strip(),
        type=payload["type"],
        state=payload.get("state", "Telangana (illustrative)"),
        district=payload.get("district", "Yadadri Bhuvanagiri"),
        mandal=payload["mandal"],
        locality=payload["locality"].strip(),
        latitude=float(payload.get("latitude") or 17.5),
        longitude=float(payload.get("longitude") or 78.9),
        address_label=payload.get("address_label", ""),
        ownership=payload.get("ownership", "Government"),
        beds=int(payload.get("beds") or 0),
        catchment_population=int(payload.get("catchment_population") or 0),
        verification_status=payload.get("verification_status", "Pending verification"),
        operating_status=payload.get("operating_status", "Operational"),
        is_active=payload.get("is_active", True),
        capacity_notes=payload.get("capacity_notes", ""),
    )
    session.add(facility)
    session.flush()
    for service_name in payload.get("services", []):
        session.add(Service(facility_id=facility.id, service_name=service_name, capacity_per_period=0))
    session.flush()
    return facility


def update_facility(session: Session, facility_id: int, changes: dict) -> Facility:
    facility = session.get(Facility, facility_id)
    if facility is None:
        raise ValueError("Facility not found")
    allowed = {"operating_status", "is_active", "verification_status", "capacity_notes", "beds", "catchment_population"}
    for key, value in changes.items():
        if key in allowed:
            setattr(facility, key, value)
    session.flush()
    return facility


def add_service(session: Session, facility_id: int, service_name: str, capacity: int, note: str = "") -> Service:
    if not service_name.strip():
        raise ValueError("Service name is required")
    service = Service(
        facility_id=facility_id, service_name=service_name.strip(),
        capacity_per_period=max(0, int(capacity)), availability_note=note or "Confirm by phone",
    )
    session.add(service)
    session.flush()
    return service


SCREENING_CAPACITY_KEYWORDS = (
    "screening", "maternal", "child", "counselling", "wellness", "nutrition",
)


def utilization_rows(session: Session, facility_ids: list[int] | None = None) -> list[dict]:
    """Camp attendance / configured preventive-service capacity, per facility.

    Documented demo formula: attendance recorded at this facility's completed
    screening events divided by the sum of active preventive/screening service
    capacity for the same facility. Operational planning indicator only; not a
    clinical quality score.
    """
    capacity_stmt = (
        select(Service.facility_id, func.sum(Service.capacity_per_period))
        .where(Service.active.is_(True))
        .where(or_(*[func.lower(Service.service_name).like(f"%{word}%") for word in SCREENING_CAPACITY_KEYWORDS]))
    )
    completed_stmt = (
        select(ScreeningEvent.facility_id, func.sum(ScreeningEvent.attendance_count))
        .where(ScreeningEvent.status == "Completed")
    )
    if facility_ids is not None:
        capacity_stmt = capacity_stmt.where(Service.facility_id.in_(facility_ids))
        completed_stmt = completed_stmt.where(ScreeningEvent.facility_id.in_(facility_ids))
    capacity = dict(session.execute(capacity_stmt.group_by(Service.facility_id)).all())
    completed = dict(session.execute(completed_stmt.group_by(ScreeningEvent.facility_id)).all())

    stmt = _facility_query()
    if facility_ids is not None:
        stmt = stmt.where(Facility.id.in_(facility_ids))
    rows = []
    for facility in session.scalars(stmt).all():
        cap = int(capacity.get(facility.id, 0) or 0)
        done = int(completed.get(facility.id, 0) or 0)
        pct = round((done / cap) * 100, 1) if cap else 0.0
        if done == 0:
            state = "No screening activity recorded"
        elif cap == 0:
            state = "No configured capacity"
        elif pct >= 90:
            state = "Near capacity"
        elif pct >= 40:
            state = "Balanced"
        else:
            state = "Spare capacity"
        rows.append({
            "facility_id": facility.id,
            "facility": facility.name,
            "type": facility.type,
            "category": category_of(facility),
            "district": facility.district,
            "mandal": facility.mandal,
            "active": "Active" if facility.is_active else "Inactive",
            "services": len(facility.services),
            "configured_capacity": cap,
            "completed_sessions": done,
            "utilization_pct": pct,
            "indicator": state,
            "operating_status": facility.operating_status,
        })
    return rows


def facility_count_by_type(session: Session, facility_ids: list[int] | None = None) -> list[dict]:
    stmt = select(Facility.type, func.count(Facility.id))
    if facility_ids is not None:
        stmt = stmt.where(Facility.id.in_(facility_ids))
    rows = session.execute(stmt.group_by(Facility.type).order_by(func.count(Facility.id).desc())).all()
    return [{"type": t, "count": c} for t, c in rows]


def referral_load_by_facility(session: Session, facility_ids: list[int] | None = None) -> list[dict]:
    stmt = (
        select(Facility.name, func.count(Referral.id))
        .join(Referral, Referral.destination_facility_id == Facility.id)
        .group_by(Facility.id)
        .order_by(func.count(Referral.id).desc())
        .limit(8)
    )
    if facility_ids is not None:
        stmt = stmt.where(Facility.id.in_(facility_ids))
    rows = session.execute(stmt).all()
    return [{"facility": name, "referrals": count} for name, count in rows]


def service_availability_matrix(session: Session, facility_ids: list[int] | None = None) -> list[dict]:
    stmt = select(Service.service_name, func.count(func.distinct(Service.facility_id)))
    if facility_ids is not None:
        stmt = stmt.where(Service.facility_id.in_(facility_ids))
    rows = session.execute(stmt.where(Service.active.is_(True)).group_by(Service.service_name).order_by(Service.service_name)).all()
    return [{"service": name, "facilities": count} for name, count in rows]
