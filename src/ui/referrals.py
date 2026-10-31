"""Referral Coordination — safe referral creation and status transitions."""
from __future__ import annotations

from datetime import date

import gradio as gr
import pandas as pd

from src.config import REFERRAL_PRIORITIES, REFERRAL_STATUSES, REFERRAL_TRANSITIONS
from src.database import session_scope
from src.models import AuditEvent
from src.services import facility_service, referral_service, reporting_service, screening_service
from src.ui.components import detail_card, kpi_cards, note, scope_controls, section

KPI_DEFS = [
    ("referrals_total", "Referrals", ""),
    ("referrals_open", "Open", "warn"),
    ("followups_overdue", "Overdue follow-ups", "alert"),
    ("followup_completion_pct", "Follow-up completion", ""),
    ("referral_completion_pct", "Referral completion", ""),
]

COLUMNS = ["referral_code", "participant", "source", "destination", "reason", "priority",
           "status", "referring_doctor", "follow_up_date", "overdue"]


def _choices(session, ids):
    rows = referral_service.list_referrals(session)
    if ids:
        allowed = set(ids)
        facilities = {f.id: f for f in facility_service.search_facilities(session)}
        rows = [r for r in rows if any(f.name == r["source"] and f.id in allowed for f in facilities.values())]
    return [(f"{r['referral_code']} — {r['participant']}", r["referral_id"]) for r in rows]


def _detail(session, referral_id):
    rows = [r for r in referral_service.list_referrals(session) if r["referral_id"] == referral_id]
    if not rows:
        return note("Select a referral.")
    r = rows[0]
    return detail_card(
        f"{r['referral_code']} — {r['participant']}",
        [
            f"Source: {r['source']} → Destination: <b>{r['destination']}</b>",
            f"Reason: {r['reason']} · Priority: <b>{r['priority']}</b> · Status: <b>{r['status']}</b>",
            f"Referring doctor: {r['referring_doctor']} · Created by: {r['created_by']}",
            f"Follow-up date: {r['follow_up_date'] or 'Not set'} · Overdue: <b>{'Yes' if r['overdue'] else 'No'}</b>",
            f"Allowed next states: {', '.join(sorted(REFERRAL_TRANSITIONS.get(r['status'], set()))) or 'none'}",
        ],
        "Urgent referrals require an emergency-capable destination. If symptoms are severe, seek emergency care "
        "immediately instead of waiting for a referral workflow.",
    )


def refresh(state, district, mandal, category, active, status, priority, overdue_only):
    args = dict(state=state, district=district, mandal=mandal, category=category, active=active)
    with session_scope() as session:
        ids = reporting_service.scope_ids(session, **args)
        kpis = reporting_service.overview_kpis(session, **args)
        rows = referral_service.list_referrals(
            session, status=status, priority=priority, overdue_only=bool(overdue_only), facility_ids=ids
        )
        choices = [(f"{r['referral_code']} — {r['participant']}", r["referral_id"]) for r in rows]
        all_choices = _choices(session, ids)
        detail_value = _detail(session, rows[0]["referral_id"]) if rows else note("No referrals match the filters.")
        available_statuses = sorted(REFERRAL_TRANSITIONS.get(rows[0]["status"], set())) if rows else []
        participants = screening_service.participant_choices(session)
        sources = [(f"{f.code} — {f.name}", f.id) for f in facility_service.search_facilities(
            session, **{k: v for k, v in args.items() if k in {"state", "district", "mandal", "category"}},
            active="Active")]
        destinations = [(f"{f.code} — {f.name} ({f.type})", f.id) for f in facility_service.search_facilities(
            session, active="Active")]
    display = dict(kpis)
    display["followup_completion_pct"] = f"{kpis['followup_completion_pct']:.1f}%"
    display["referral_completion_pct"] = f"{kpis['referral_completion_pct']:.1f}%"
    return (
        kpi_cards(display, KPI_DEFS),
        pd.DataFrame(rows, columns=COLUMNS),
        gr.update(choices=choices, value=choices[0][1] if choices else None),
        gr.update(choices=all_choices, value=all_choices[0][1] if all_choices else None),
        gr.update(choices=available_statuses, value=available_statuses[0] if available_statuses else None),
        detail_value,
        gr.update(choices=participants, value=participants[0][1] if participants else None),
        gr.update(choices=sources, value=sources[0][1] if sources else None),
        gr.update(choices=destinations, value=destinations[0][1] if destinations else None),
        note(reporting_service.scope_label(state, district, mandal, category, active)),
    )


def _transition_choices(referral_id):
    if not referral_id:
        return gr.update(choices=[], value=None)
    with session_scope() as session:
        rows = [r for r in referral_service.list_referrals(session) if r["referral_id"] == int(referral_id)]
    if not rows:
        return gr.update(choices=[], value=None)
    values = sorted(REFERRAL_TRANSITIONS.get(rows[0]["status"], set()))
    return gr.update(choices=values, value=values[0] if values else None)


def _create(participant_id, source_id, destination_id, reason, priority, follow_up, doctor):
    if not participant_id or not source_id or not destination_id:
        return "Choose participant, source and destination.", gr.skip(), gr.skip()
    try:
        due = date.fromisoformat(follow_up.strip()) if follow_up and follow_up.strip() else None
        with session_scope() as session:
            referral = referral_service.create_referral(
                session, int(participant_id), int(source_id), int(destination_id), reason,
                priority, follow_up_date=due, referring_doctor=doctor or "Demo clinician",
            )
            session.add(AuditEvent(
                actor_role="Medical Officer", action="Created referral",
                entity_type="referral", entity_id=referral.referral_code, note=reason,
            ))
            rows = referral_service.list_referrals(session)
            choices = [(f"{r['referral_code']} — {r['participant']}", r["referral_id"]) for r in rows]
        return (
            f"Referral {referral.referral_code} created in Draft status. Send it after review.",
            pd.DataFrame(rows, columns=COLUMNS),
            gr.update(choices=choices, value=referral.id),
        )
    except Exception as exc:  # noqa: BLE001
        return f"Could not create referral: {exc}", gr.skip(), gr.skip()


def _transition(referral_id, new_status, note_text):
    if not referral_id:
        return "Select a referral.", gr.skip(), gr.skip()
    try:
        with session_scope() as session:
            referral = referral_service.transition_referral(session, int(referral_id), new_status, note_text or "")
            session.add(AuditEvent(
                actor_role="Medical Officer", action=f"Referral → {new_status}",
                entity_type="referral", entity_id=referral.referral_code, note=note_text or "",
            ))
            rows = referral_service.list_referrals(session)
            choices = [(f"{r['referral_code']} — {r['participant']}", r["referral_id"]) for r in rows]
            detail_value = _detail(session, referral.id)
            available = sorted(REFERRAL_TRANSITIONS.get(referral.status, set()))
        return (
            f"Referral {referral.referral_code} moved to '{referral.status}'.",
            pd.DataFrame(rows, columns=COLUMNS),
            gr.update(choices=choices, value=referral.id),
            detail_value,
            gr.update(choices=available, value=available[0] if available else None),
        )
    except Exception as exc:  # noqa: BLE001
        return f"Could not transition referral: {exc}", gr.skip(), gr.skip(), gr.skip(), gr.skip()


def build(demo) -> None:
    gr.HTML(section("Referral Coordination"))
    gr.HTML(note(
        "Referrals move through explicit transitions. Urgent cases are only accepted by emergency-capable "
        "destinations. This workflow is administrative and never replaces emergency care."
    ))
    controls = scope_controls(active_default="Active")
    with gr.Row():
        status = gr.Dropdown(["All"] + REFERRAL_STATUSES, value="All", label="Status")
        priority = gr.Dropdown(["All"] + REFERRAL_PRIORITIES, value="All", label="Priority")
        overdue = gr.Checkbox(label="Overdue follow-up only", value=False)
        btn = gr.Button("Apply referral filters", variant="primary")
    kpis = gr.HTML()
    scope_note = gr.HTML()
    table = gr.Dataframe(interactive=False, wrap=True, label="Referral worklist")
    with gr.Row():
        with gr.Column(scale=3):
            detail_choice = gr.Dropdown(label="Referral detail", choices=[])
            detail_html = gr.HTML()
        with gr.Column(scale=2):
            gr.HTML(section("Update referral status"))
            transition_choice = gr.Dropdown(label="Referral", choices=[])
            transition_status = gr.Dropdown(label="Next status", choices=[])
            closure_note = gr.Textbox(label="Closure / transition note", lines=2)
            transition_btn = gr.Button("Apply transition", variant="primary")
            transition_msg = gr.Markdown()

    with gr.Accordion("Create a referral", open=False):
        gr.HTML(note(
            "Urgent referrals are validated against emergency capability. Choose the correct destination level; "
            "do not divert urgent symptoms to a facility without emergency support."
        ))
        with gr.Row():
            participant = gr.Dropdown(label="Participant", choices=[])
            source = gr.Dropdown(label="Source facility", choices=[])
            destination = gr.Dropdown(label="Destination facility", choices=[])
        with gr.Row():
            reason = gr.Textbox(label="Reason category", placeholder="e.g. Elevated blood pressure — clinical review")
            r_priority = gr.Dropdown(REFERRAL_PRIORITIES, value="Routine", label="Priority")
            follow_up = gr.Textbox(label="Follow-up date (YYYY-MM-DD, optional)")
            doctor = gr.Textbox(label="Referring doctor alias", value="Dr. Rao (alias)")
        create_btn = gr.Button("Create referral", variant="primary")
        create_msg = gr.Markdown()

    outputs = [kpis, table, detail_choice, transition_choice, transition_status, detail_html,
               participant, source, destination, scope_note]
    btn.click(refresh, inputs=list(controls) + [status, priority, overdue], outputs=outputs)
    detail_choice.change(lambda rid: _detail_for(rid), inputs=[detail_choice], outputs=[detail_html])
    transition_choice.change(
        _transition_choices, inputs=[transition_choice], outputs=[transition_status]
    )
    transition_btn.click(
        _transition, inputs=[transition_choice, transition_status, closure_note],
        outputs=[transition_msg, table, transition_choice, detail_html, transition_status],
    )
    create_btn.click(
        _create, inputs=[participant, source, destination, reason, r_priority, follow_up, doctor],
        outputs=[create_msg, table, transition_choice],
    )
    demo.load(refresh, inputs=list(controls) + [status, priority, overdue], outputs=outputs)


def _detail_for(referral_id):
    if not referral_id:
        return note("Select a referral.")
    with session_scope() as session:
        return _detail(session, int(referral_id))
