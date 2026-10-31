"""Awareness campaigns and administrative notification drafts.

No message is ever really sent. Delivery states are simulated and clearly
labelled so that no real person is contacted by this prototype.
"""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from src.config import CAMPAIGN_CHANNELS, CAMPAIGN_STATUSES, NOTIFICATION_CHANNELS, NOTIFICATION_STATUSES
from src.models import Campaign, Facility, Notification
from src.models.base import utcnow


def list_campaigns(session: Session, status: str = "All", channel: str = "All") -> list[dict]:
    stmt = select(Campaign).order_by(Campaign.schedule_at)
    if status and status != "All":
        stmt = stmt.where(Campaign.status == status)
    if channel and channel != "All":
        stmt = stmt.where(Campaign.planned_channel == channel)
    rows = session.scalars(stmt).all()
    return [
        {
            "campaign_id": c.id, "title": c.title, "message": c.message,
            "language": c.language, "audience": c.audience, "target_area": c.target_area,
            "channel": c.planned_channel,
            "schedule": c.schedule_at.strftime("%Y-%m-%d %H:%M"),
            "status": c.status, "delivery": c.delivery_status, "created_by": c.created_by,
        }
        for c in rows
    ]


def create_campaign(
    session: Session,
    title: str,
    message: str,
    language: str,
    audience: str,
    target_area: str,
    channel: str,
    schedule_at: datetime | None = None,
    created_by: str = "Demo user",
) -> Campaign:
    if not title.strip():
        raise ValueError("Campaign title is required")
    if not message.strip():
        raise ValueError("Campaign message is required")
    if channel not in CAMPAIGN_CHANNELS:
        raise ValueError("Invalid channel")
    campaign = Campaign(
        title=title.strip(), message=message.strip(), language=language.strip() or "Telugu",
        audience=audience.strip() or "General community", target_area=target_area.strip() or "Unspecified",
        planned_channel=channel, schedule_at=schedule_at or utcnow(),
        status="Draft", delivery_status="Simulated — not sent", created_by=created_by,
    )
    session.add(campaign)
    session.flush()
    return campaign


def update_campaign_status(session: Session, campaign_id: int, status: str) -> Campaign:
    campaign = session.get(Campaign, campaign_id)
    if campaign is None:
        raise ValueError("Campaign not found")
    if status not in CAMPAIGN_STATUSES:
        raise ValueError("Invalid campaign status")
    campaign.status = status
    if status == "Scheduled (simulated)":
        campaign.delivery_status = "Simulated schedule — not sent"
    session.flush()
    return campaign


def campaign_choices(session: Session) -> list[tuple[str, int]]:
    return [(c["title"], c["campaign_id"]) for c in list_campaigns(session)]


def list_notifications(session: Session, status: str = "All", channel: str = "All") -> list[dict]:
    stmt = select(Notification).order_by(Notification.schedule_at.desc())
    if status and status != "All":
        stmt = stmt.where(Notification.status == status)
    if channel and channel != "All":
        stmt = stmt.where(Notification.channel == channel)
    rows = session.scalars(stmt).all()
    return [
        {
            "notification_id": n.id, "title": n.title, "message": n.message,
            "audience": n.audience, "channel": n.channel, "status": n.status,
            "related_entity": n.related_entity,
            "schedule": n.schedule_at.strftime("%Y-%m-%d %H:%M"),
            "created_by": n.created_by,
        }
        for n in rows
    ]


def create_notification(
    session: Session,
    title: str,
    message: str,
    audience: str,
    channel: str,
    related_entity: str = "",
    schedule_at: datetime | None = None,
    created_by: str = "Demo user",
) -> Notification:
    if not title.strip():
        raise ValueError("Notification title is required")
    if not message.strip():
        raise ValueError("Notification message is required")
    if channel not in NOTIFICATION_CHANNELS:
        raise ValueError("Invalid channel")
    notification = Notification(
        title=title.strip(), message=message.strip(), audience=audience.strip() or "Facility administrators",
        channel=channel, status="Draft", related_entity=related_entity.strip(),
        schedule_at=schedule_at or utcnow(), created_by=created_by,
    )
    session.add(notification)
    session.flush()
    return notification


def update_notification_status(session: Session, notification_id: int, status: str) -> Notification:
    notification = session.get(Notification, notification_id)
    if notification is None:
        raise ValueError("Notification not found")
    if status not in NOTIFICATION_STATUSES:
        raise ValueError("Invalid notification status")
    notification.status = status
    session.flush()
    return notification


def notification_choices(session: Session) -> list[tuple[str, int]]:
    return [(n["title"] + " — " + n["status"], n["notification_id"]) for n in list_notifications(session)]


def communication_summary(session: Session) -> dict[str, int]:
    campaigns = session.scalars(select(Campaign)).all()
    notifications = session.scalars(select(Notification)).all()
    return {
        "campaigns": len(campaigns),
        "campaigns_live": sum(1 for c in campaigns if c.status == "Scheduled (simulated)"),
        "campaigns_draft": sum(1 for c in campaigns if c.status in {"Draft", "Needs review"}),
        "notifications": len(notifications),
        "notifications_approved": sum(1 for n in notifications if n.status == "Approved"),
        "notifications_simulated": sum(1 for n in notifications if n.status == "Simulated — sent"),
        "delivered_for_real": 0,
    }


def facility_names(session: Session) -> dict[int, str]:
    return dict(session.execute(select(Facility.id, Facility.name)).all())
