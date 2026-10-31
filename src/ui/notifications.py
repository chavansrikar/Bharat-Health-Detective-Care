"""Notification Management — internal operational notification drafts."""
from __future__ import annotations

from datetime import datetime, timedelta

import gradio as gr
import pandas as pd

from src.config import NOTIFICATION_CHANNELS, NOTIFICATION_STATUSES
from src.database import session_scope
from src.models import AuditEvent
from src.services import notification_service
from src.ui.components import kpi_cards, note, section

KPI_DEFS = [
    ("notifications", "Notifications", ""),
    ("notifications_approved", "Approved", ""),
    ("notifications_simulated", "Simulated sent", ""),
    ("campaigns", "Campaigns", ""),
    ("delivered_for_real", "Really delivered", "alert"),
]

COLUMNS = ["title", "audience", "channel", "status", "related_entity", "schedule", "message"]


def _schedule(value: str):
    if not value or not value.strip():
        return datetime.now()
    for fmt in ("%Y-%m-%d %H:%M", "%Y-%m-%d"):
        try:
            return datetime.strptime(value.strip(), fmt)
        except ValueError:
            continue
    raise ValueError("Enter schedule as YYYY-MM-DD or YYYY-MM-DD HH:MM")


def refresh(status, related):
    with session_scope() as session:
        summary = notification_service.communication_summary(session)
        rows = notification_service.list_notifications(session)
        if status != "All":
            rows = [r for r in rows if r["status"] == status]
        if related != "All":
            rows = [r for r in rows if r["related_entity"] == related]
        choices = [(r["title"] + " — " + r["status"], r["notification_id"]) for r in rows]
    display = dict(summary)
    display["delivered_for_real"] = "0"
    return (
        kpi_cards(display, KPI_DEFS),
        pd.DataFrame(rows, columns=COLUMNS),
        gr.update(choices=choices, value=choices[0][1] if choices else None),
    )


def _create(title, message, audience, channel, related, schedule, actor):
    try:
        when = _schedule(schedule)
        with session_scope() as session:
            notification = notification_service.create_notification(
                session, title, message, audience, channel, related, when, created_by=actor or "Demo user"
            )
            session.add(AuditEvent(
                actor_role=actor or "Demo user", action="Created notification draft",
                entity_type="notification", entity_id=str(notification.id), note=notification.title,
            ))
            rows = notification_service.list_notifications(session)
            choices = [(r["title"] + " — " + r["status"], r["notification_id"]) for r in rows]
        return (
            f"Notification '{notification.title}' created as a draft. Nothing was sent.",
            pd.DataFrame(rows, columns=COLUMNS),
            gr.update(choices=choices, value=notification.id),
        )
    except Exception as exc:  # noqa: BLE001
        return f"Could not create notification: {exc}", gr.skip(), gr.skip()


def _update(notification_id, status):
    if not notification_id:
        return "Select a notification."
    try:
        with session_scope() as session:
            notification = notification_service.update_notification_status(session, int(notification_id), status)
            session.add(AuditEvent(
                actor_role="District Administrator", action=f"Notification status → {status}",
                entity_type="notification", entity_id=str(notification.id), note=notification.title,
            ))
        return f"Notification set to '{notification.status}'. Delivery remains simulated only."
    except Exception as exc:  # noqa: BLE001
        return f"Could not update notification: {exc}"


def build(demo) -> None:
    gr.HTML(section("Notification Management"))
    gr.HTML(note(
        "Internal notification drafts for administrators and facility teams. Approving a notification records a "
        "demo state only; no SMS, WhatsApp or voice call is actually dispatched without a consented integration."
    ))
    with gr.Row():
        status = gr.Dropdown(["All"] + NOTIFICATION_STATUSES, value="All", label="Status")
        related = gr.Dropdown(
            ["All", "referral", "lab_order", "facility", "screening_event", "vacancy", "screening"],
            value="All", label="Related entity",
        )
        btn = gr.Button("Apply notification filters", variant="primary")
    kpis = gr.HTML()
    table = gr.Dataframe(interactive=False, wrap=True, label="Notification register")

    with gr.Row():
        with gr.Column(scale=3):
            with gr.Accordion("Create a notification draft", open=True):
                title = gr.Textbox(label="Title")
                message = gr.Textbox(label="Message", lines=4)
                audience = gr.Textbox(label="Audience", value="Facility administrators")
                channel = gr.Dropdown(NOTIFICATION_CHANNELS, value=NOTIFICATION_CHANNELS[0], label="Channel")
                related_value = gr.Dropdown(
                    ["referral", "lab_order", "facility", "screening_event", "vacancy", "screening", "campaign"],
                    value="referral", label="Related entity",
                )
                schedule = gr.Textbox(label="Schedule (YYYY-MM-DD HH:MM)",
                                      value=(datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d 09:00"))
                actor = gr.Textbox(label="Created by (demo alias)", value="Demo administrator")
                create_btn = gr.Button("Create notification draft", variant="primary")
                create_msg = gr.Markdown()
        with gr.Column(scale=2):
            gr.HTML(section("Notification workflow"))
            gr.HTML(note("Draft → Approved → Simulated — sent, or Cancelled. No real delivery is performed."))
            choice = gr.Dropdown(label="Notification", choices=[])
            new_status = gr.Dropdown(NOTIFICATION_STATUSES, value="Approved", label="New status")
            update_btn = gr.Button("Update notification status")
            update_msg = gr.Markdown()

    outputs = [kpis, table, choice]
    btn.click(refresh, inputs=[status, related], outputs=outputs)
    create_btn.click(
        _create, inputs=[title, message, audience, channel, related_value, schedule, actor],
        outputs=[create_msg, table, choice],
    )
    update_btn.click(_update, inputs=[choice, new_status], outputs=[update_msg])
    demo.load(refresh, inputs=[status, related], outputs=outputs)
