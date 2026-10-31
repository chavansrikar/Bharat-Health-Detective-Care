"""Substance-Use Prevention — voluntary, confidential counselling support."""
from __future__ import annotations

from datetime import datetime

import gradio as gr
import pandas as pd
import plotly.express as px

from src.config import SUBSTANCE_STATUSES
from src.database import session_scope
from src.models import AuditEvent
from src.services import screening_service, substance_service
from src.ui.components import kpi_cards, note, section

KPI_DEFS = [
    ("cases", "Support cases", ""),
    ("consented", "Consent recorded", ""),
    ("scheduled", "Counselling scheduled", ""),
    ("completed", "Counselling completed", ""),
    ("referred", "Referred to care", ""),
]

COLUMNS = ["case_code", "participant", "substance_category", "consent", "confidentiality",
           "counselling_status", "assigned_counsellor", "follow_up_date"]


def _parse_follow_up(value: str):
    if not value or not value.strip():
        return None
    for fmt in ("%Y-%m-%d %H:%M", "%Y-%m-%d"):
        try:
            return datetime.strptime(value.strip(), fmt)
        except ValueError:
            continue
    raise ValueError("Enter follow-up as YYYY-MM-DD or YYYY-MM-DD HH:MM")


def refresh(status, text):
    with session_scope() as session:
        summary = substance_service.summary(session)
        rows = substance_service.list_cases(session, status=status, text=text or "")
        distribution = substance_service.substance_distribution(session)
        participants = screening_service.participant_choices(session)
        all_choices = substance_service.case_choices(session)
    if not distribution:
        chart = px.bar(title="No support cases in the demo dataset")
    else:
        chart = px.bar(
            pd.DataFrame(distribution), x="cases", y="substance_category", orientation="h",
            title="Support cases by substance category (aggregate demo counts)",
        )
        chart.update_layout(height=320, margin=dict(l=10, r=16, t=44, b=10),
                            yaxis_title="", xaxis_title="Cases")
    return (
        kpi_cards(summary, KPI_DEFS),
        pd.DataFrame(rows, columns=COLUMNS),
        chart,
        gr.update(choices=participants, value=participants[0][1] if participants else None),
        gr.update(choices=all_choices, value=all_choices[0][1] if all_choices else None),
    )


def _create(participant_id, category, note_text, consent, counsellor, follow_up):
    if not participant_id:
        return "Choose a participant.", gr.skip(), gr.skip()
    try:
        when = _parse_follow_up(follow_up)
        with session_scope() as session:
            case = substance_service.create_case(
                session, int(participant_id), category, note_text, consent,
                counsellor or "Unassigned", when,
            )
            session.add(AuditEvent(
                actor_role="Counselling team", action="Created confidential support case",
                entity_type="substance_case", entity_id=case.case_code, note=case.substance_category,
            ))
            rows = substance_service.list_cases(session)
            choices = substance_service.case_choices(session)
        return (
            f"Confidential support case {case.case_code} created. Voluntary, non-punitive support only.",
            pd.DataFrame(rows, columns=COLUMNS),
            gr.update(choices=choices, value=case.id),
        )
    except Exception as exc:  # noqa: BLE001
        return f"Could not create support case: {exc}", gr.skip(), gr.skip()


def _update(case_id, status, counsellor, note_text):
    if not case_id:
        return "Select a support case.", gr.skip()
    try:
        with session_scope() as session:
            case = substance_service.update_case(
                session, int(case_id), status=status or None,
                counsellor=counsellor or None, note=note_text or None,
            )
            session.add(AuditEvent(
                actor_role="Counselling team", action="Updated confidential support case",
                entity_type="substance_case", entity_id=case.case_code, note=case.counselling_status,
            ))
            rows = substance_service.list_cases(session)
        return f"Support case {case.case_code} updated to '{case.counselling_status}'.", pd.DataFrame(rows, columns=COLUMNS)
    except Exception as exc:  # noqa: BLE001
        return f"Could not update support case: {exc}", gr.skip()


def build(demo) -> None:
    gr.HTML(section("Substance-Use Prevention"))
    gr.HTML(note(
        "Voluntary, confidential and non-punitive support. Participation requires recorded consent. This module "
        "does not support enforcement, criminal, employment or disciplinary action, and it never labels a person. "
        "Clinical care decisions remain with qualified clinicians."
    ))
    with gr.Row():
        status = gr.Dropdown(["All"] + SUBSTANCE_STATUSES, value="All", label="Counselling status")
        text = gr.Textbox(label="Search case code, category or participant", scale=2)
        btn = gr.Button("Apply filters", variant="primary")
    kpis = gr.HTML()
    table = gr.Dataframe(interactive=False, wrap=True, label="Confidential support cases")
    chart = gr.Plot(label="Aggregate demand view")
    with gr.Row():
        with gr.Column(scale=3):
            with gr.Accordion("Create a voluntary support case", open=False):
                participant = gr.Dropdown(label="Participant (synthetic code only)", choices=[])
                category = gr.Textbox(label="Substance category", placeholder="e.g. Tobacco, Alcohol")
                note_text = gr.Textbox(label="Screening / support note", lines=2)
                consent = gr.Dropdown(["Granted (demo)", "Declined (demo)"], value="Granted (demo)", label="Consent")
                counsellor = gr.Textbox(label="Assigned counsellor", value="Counsellor (alias)")
                follow_up = gr.Textbox(label="Follow-up (YYYY-MM-DD, optional)")
                create_btn = gr.Button("Create support case", variant="primary")
                create_msg = gr.Markdown()
        with gr.Column(scale=2):
            with gr.Accordion("Update support case", open=True):
                choice = gr.Dropdown(label="Support case", choices=[])
                new_status = gr.Dropdown(SUBSTANCE_STATUSES, value="Counselling scheduled", label="New status")
                new_counsellor = gr.Textbox(label="Counsellor alias", placeholder="Leave blank to keep")
                new_note = gr.Textbox(label="Update note", lines=2, placeholder="Leave blank to keep")
                update_btn = gr.Button("Update case")
                update_msg = gr.Markdown()

    outputs = [kpis, table, chart, participant, choice]
    btn.click(refresh, inputs=[status, text], outputs=outputs)
    create_btn.click(
        _create, inputs=[participant, category, note_text, consent, counsellor, follow_up],
        outputs=[create_msg, table, choice],
    )
    update_btn.click(
        _update, inputs=[choice, new_status, new_counsellor, new_note],
        outputs=[update_msg, table],
    )
    demo.load(refresh, inputs=[status, text], outputs=outputs)
