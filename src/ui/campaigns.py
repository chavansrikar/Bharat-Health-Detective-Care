"""Health Awareness Campaigns — approved drafts and simulated scheduling."""
from __future__ import annotations

from datetime import datetime, timedelta

import gradio as gr
import pandas as pd

from src.config import CAMPAIGN_CHANNELS, CAMPAIGN_STATUSES, DISTRICTS
from src.database import session_scope
from src.models import AuditEvent
from src.services import ai_service, notification_service
from src.ui.components import kpi_cards, note, section

KPI_DEFS = [
    ("campaigns", "Campaigns", ""),
    ("campaigns_live", "Simulated scheduled", ""),
    ("campaigns_draft", "Draft / needs review", "warn"),
    ("notifications", "Notifications", ""),
    ("delivered_for_real", "Really delivered", "alert"),
]

COLUMNS = ["title", "language", "audience", "target_area", "channel", "schedule", "status", "delivery"]


def _schedule(value: str):
    if not value or not value.strip():
        return datetime.now() + timedelta(days=7)
    for fmt in ("%Y-%m-%d %H:%M", "%Y-%m-%d"):
        try:
            return datetime.strptime(value.strip(), fmt)
        except ValueError:
            continue
    raise ValueError("Enter schedule as YYYY-MM-DD or YYYY-MM-DD HH:MM")


def refresh():
    with session_scope() as session:
        summary = notification_service.communication_summary(session)
        rows = notification_service.list_campaigns(session)
        choices = notification_service.campaign_choices(session)
    display = dict(summary)
    display["delivered_for_real"] = "0"
    return (
        kpi_cards(display, KPI_DEFS),
        pd.DataFrame(rows, columns=COLUMNS),
        gr.update(choices=choices, value=choices[0][1] if choices else None),
    )


def _create(title, message, language, audience, area, channel, schedule, actor):
    try:
        when = _schedule(schedule)
        if not title.strip():
            raise ValueError("Campaign title is required")
        with session_scope() as session:
            campaign = notification_service.create_campaign(
                session, title, message, language, audience, area, channel, when, created_by=actor or "Demo user"
            )
            session.add(AuditEvent(
                actor_role=actor or "Demo user", action="Created awareness campaign",
                entity_type="campaign", entity_id=str(campaign.id), note=campaign.title,
            ))
            rows = notification_service.list_campaigns(session)
            choices = notification_service.campaign_choices(session)
        return (
            f"Campaign '{campaign.title}' created as a draft. No message has been sent to any person.",
            pd.DataFrame(rows, columns=COLUMNS),
            gr.update(choices=choices, value=campaign.id),
        )
    except Exception as exc:  # noqa: BLE001
        return f"Could not create campaign: {exc}", gr.skip(), gr.skip()


def _update(campaign_id, status):
    if not campaign_id:
        return "Select a campaign.", gr.skip()
    try:
        with session_scope() as session:
            campaign = notification_service.update_campaign_status(session, int(campaign_id), status)
            session.add(AuditEvent(
                actor_role="District Administrator", action=f"Campaign status → {status}",
                entity_type="campaign", entity_id=str(campaign.id), note=campaign.title,
            ))
            rows = notification_service.list_campaigns(session)
        return f"Campaign '{campaign.title}' set to '{campaign.status}' (simulated only).", pd.DataFrame(rows, columns=COLUMNS)
    except Exception as exc:  # noqa: BLE001
        return f"Could not update campaign: {exc}", gr.skip()


def _draft(topic, audience, language):
    return ai_service.campaign_draft(topic or "", audience or "", language or "Telugu")


def build(demo) -> None:
    gr.HTML(section("Health Awareness Campaigns"))
    gr.HTML(note(
        "Campaigns are drafts for human review. Scheduling is simulated and nothing is sent to real recipients. "
        "Messages must avoid diagnosis, stigma and guaranteed outcomes; emergency advice is always included."
    ))
    kpis = gr.HTML()
    table = gr.Dataframe(interactive=False, wrap=True, label="Campaign register")

    with gr.Row():
        with gr.Column(scale=3):
            with gr.Accordion("Create an awareness campaign", open=True):
                title = gr.Textbox(label="Campaign title")
                language = gr.Textbox(label="Language", value="Telugu")
                audience = gr.Textbox(label="Audience", value="General community")
                area = gr.Dropdown(DISTRICTS, value=DISTRICTS[0], label="Target area")
                channel = gr.Dropdown(CAMPAIGN_CHANNELS, value=CAMPAIGN_CHANNELS[0], label="Planned channel")
                schedule = gr.Textbox(label="Schedule (YYYY-MM-DD HH:MM)",
                                      value=(datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d 10:00"))
                message = gr.Textbox(label="Message", lines=4)
                creator = gr.Textbox(label="Created by (demo alias)", value="Demo administrator")
                with gr.Row():
                    draft_btn = gr.Button("Draft message assistance")
                    create_btn = gr.Button("Create campaign draft", variant="primary")
                create_msg = gr.Markdown()
        with gr.Column(scale=2):
            gr.HTML(section("Campaign workflow"))
            gr.HTML(note(
                "Draft → Needs review → Approved draft → Scheduled (simulated). Status changes do not send messages."
            ))
            choice = gr.Dropdown(label="Campaign", choices=[])
            status = gr.Dropdown(CAMPAIGN_STATUSES, value="Needs review", label="New status")
            update_btn = gr.Button("Update campaign status")
            update_msg = gr.Markdown()

    outputs = [kpis, table, choice]
    draft_btn.click(_draft, inputs=[title, audience, language], outputs=[message])
    create_btn.click(
        _create, inputs=[title, message, language, audience, area, channel, schedule, creator],
        outputs=[create_msg, table, choice],
    )
    update_btn.click(_update, inputs=[choice, status], outputs=[update_msg, table])
    demo.load(refresh, outputs=outputs)
