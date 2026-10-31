"""Administration and Settings — demo governance, audit and data controls."""
from __future__ import annotations

import gradio as gr
import pandas as pd
from sqlalchemy import func, select

from src.config import (
    AI_ENABLED,
    APP_NAME,
    DATABASE_URL,
    DEMO_ROLES,
    DISTRICTS,
    SIMULATED_BANNER,
)
from src.database import session_scope
from src.models import (
    Appointment,
    AuditEvent,
    Campaign,
    EmploymentApplication,
    Facility,
    LabOrder,
    Notification,
    Participant,
    Programme,
    Referral,
    Screening,
    ScreeningEvent,
    Service,
    Staff,
    StaffVacancy,
    SubstanceUseCase,
)
from src.seed import reset_database
from src.ui.components import note, section

COUNT_MODELS = [
    ("Facilities", Facility), ("Services", Service), ("People", Participant),
    ("Programmes", Programme), ("Screening events", ScreeningEvent), ("Screenings", Screening),
    ("Referrals", Referral), ("Lab orders", LabOrder), ("Staff", Staff),
    ("Vacancies", StaffVacancy), ("Applications", EmploymentApplication),
    ("Campaigns", Campaign), ("Notifications", Notification),
    ("Substance support cases", SubstanceUseCase), ("Appointments", Appointment),
    ("Audit events", AuditEvent),
]

AUDIT_COLUMNS = ["created_at", "actor_role", "action", "entity_type", "entity_id", "note"]


def _counts(session):
    return {label: int(session.scalar(select(func.count()).select_from(model)) or 0) for label, model in COUNT_MODELS}


def _audit(session):
    rows = session.scalars(select(AuditEvent).order_by(AuditEvent.created_at.desc()).limit(60)).all()
    return [
        {
            "created_at": row.created_at.strftime("%Y-%m-%d %H:%M"),
            "actor_role": row.actor_role, "action": row.action,
            "entity_type": row.entity_type, "entity_id": row.entity_id, "note": row.note,
        }
        for row in rows
    ]


def _settings_html(counts):
    return f"""
    <div class="bhd-detail">
      <div class="t">Environment &amp; safety configuration</div>
      <div><b>Application:</b> {APP_NAME}</div>
      <div><b>Database:</b> local SQLite ({DATABASE_URL.split('///')[-1]})</div>
      <div><b>Demo geographies:</b> {', '.join(DISTRICTS)}</div>
      <div><b>Roles available (demo switcher):</b> {', '.join(DEMO_ROLES)}</div>
      <div><b>AI assistance:</b> {'enabled' if AI_ENABLED else 'disabled — deterministic fallbacks only'}</div>
      <div><b>Real message delivery:</b> none. All campaigns and notifications are drafts or simulated.</div>
      <div><b>Dataset:</b> {counts.get('Facilities', 0)} facilities · {counts.get('People', 0)} people ·
      {counts.get('Referrals', 0)} referrals · {counts.get('Lab orders', 0)} lab orders</div>
      <div class="f">{SIMULATED_BANNER}</div>
    </div>
    """


def refresh():
    with session_scope() as session:
        counts = _counts(session)
        audit = pd.DataFrame(_audit(session), columns=AUDIT_COLUMNS)
        role_rows = [
            {"role": role, "access": _role_access(role)} for role in DEMO_ROLES
        ]
    return (
        _settings_html(counts),
        pd.DataFrame([{"dataset": k, "rows": v} for k, v in counts.items()]),
        audit,
        pd.DataFrame(role_rows, columns=["role", "access"]),
    )


def _role_access(role: str) -> str:
    mapping = {
        "District Administrator": "Full district operations workspace, reports and administration",
        "State Health Administrator": "State-wide operations workspace, reports and administration",
        "District Medical Officer": "Clinical review, referrals, programmes, diagnostics and reports",
        "Facility Administrator": "Facility infrastructure, workforce, diagnostics and local reports",
        "Medical Officer": "Screening review, referrals, diagnostics and citizen records",
        "Laboratory Administrator": "Diagnostic laboratory workflow and reports",
        "Community Health Worker": "Registry, screening, referrals, campaigns and citizen support",
        "Citizen": "Citizen Portal and facility locator only",
    }
    return mapping.get(role, "Demo workspace access")


def _reset(confirm: str):
    if (confirm or "").strip().upper() != "RESET":
        return "Type RESET in the confirmation box to restore the demo dataset.", gr.skip(), gr.skip(), gr.skip()
    with session_scope() as session:
        reset_database(session)
        counts = _counts(session)
        audit = pd.DataFrame(_audit(session), columns=AUDIT_COLUMNS)
    return (
        "Demo dataset restored to the deterministic seed. Existing demo edits were removed.",
        _settings_html(counts),
        pd.DataFrame([{"dataset": k, "rows": v} for k, v in counts.items()]),
        audit,
    )


def build(demo) -> None:
    gr.HTML(section("Administration and Settings"))
    gr.HTML(note(
        "Demo governance view. The role switcher is not authentication and must never be treated as access control "
        "in a real deployment. No secrets, real patient data or live messaging credentials are stored here."
    ))
    settings = gr.HTML()
    counts_table = gr.Dataframe(interactive=False, wrap=True, label="Dataset row counts")
    with gr.Accordion("Role access matrix (demo)", open=False):
        role_table = gr.Dataframe(interactive=False, wrap=True, label="Role intent")
    gr.HTML(section("Activity log"))
    gr.HTML(note(
        "Recent in-app actions are recorded locally for demonstration. In production, audit logs require retention, "
        "access control and tamper-evident storage."
    ))
    audit_table = gr.Dataframe(interactive=False, wrap=True, label="Audit events")

    gr.HTML(section("Reset demo data"))
    with gr.Row():
        confirm = gr.Textbox(label="Type RESET to confirm", scale=2)
        reset_btn = gr.Button("Restore deterministic demo dataset", variant="primary")
    reset_msg = gr.Markdown()

    outputs = [settings, counts_table, audit_table, role_table]
    reset_btn.click(_reset, inputs=[confirm], outputs=[reset_msg, settings, counts_table, audit_table])
    demo.load(refresh, outputs=outputs)
