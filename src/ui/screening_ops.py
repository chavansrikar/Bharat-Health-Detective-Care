"""Screening Operations — camps, observations and clinician review queue."""
from __future__ import annotations

import gradio as gr
import pandas as pd

from src.config import RESULT_CATEGORIES
from src.database import session_scope
from src.models import AuditEvent
from src.services import reporting_service, screening_service
from src.ui.components import kpi_cards, note, scope_controls, section

KPI_DEFS = [
    ("screening_events", "Screening events", ""),
    ("screening_activities", "Observations", ""),
    ("pending_reviews", "Awaiting review", "warn"),
    ("screening_review_pct", "Review completion", ""),
    ("screenings", "Participants screened", ""),
]

QUEUE_COLUMNS = ["screening_id", "participant", "event", "screening_type", "result_category", "review_status"]
ALL_COLUMNS = ["screening_id", "participant", "event", "screening_type", "result_category", "review_status", "reviewed_by"]


def refresh(state, district, mandal, category, active):
    args = dict(state=state, district=district, mandal=mandal, category=category, active=active)
    with session_scope() as session:
        ids = reporting_service.scope_ids(session, **args)
        kpis = reporting_service.overview_kpis(session, **args)
        queue = screening_service.review_queue(session)
        all_rows = screening_service.all_screenings(session)
        if ids:
            event_ids = {e["event_id"] for e in screening_service.list_events(session, facility_ids=ids)}
            queue = [row for row in queue if _event_id(row, session) in event_ids]
            all_rows = [row for row in all_rows if _event_id(row, session) in event_ids]
        events = screening_service.facility_event_choices(session, facility_ids=ids)
        participants = screening_service.participant_choices(session)
    display = dict(kpis)
    display["screening_review_pct"] = f"{kpis['screening_review_pct']:.1f}%"
    pending_choices = [(f"SC-{row['screening_id']:04d} — {row['participant']}", row["screening_id"]) for row in queue]
    return (
        kpi_cards(display, KPI_DEFS),
        pd.DataFrame(queue, columns=QUEUE_COLUMNS),
        pd.DataFrame(all_rows, columns=ALL_COLUMNS),
        gr.update(choices=events, value=events[0][1] if events else None),
        gr.update(choices=participants, value=participants[0][1] if participants else None),
        gr.update(choices=pending_choices, value=pending_choices[0][1] if pending_choices else None),
        note(reporting_service.scope_label(state, district, mandal, category, active)),
    )


def _event_id(row: dict, session) -> int:
    from src.models import Screening
    record = session.get(Screening, row["screening_id"])
    return record.event_id if record else -1


def _record(participant_id, event_id, screening_type, observation, result_category):
    if not participant_id or not event_id:
        return "Choose a participant and a screening event.", gr.skip()
    try:
        with session_scope() as session:
            screening = screening_service.record_screening(
                session, int(participant_id), int(event_id), screening_type, observation, result_category
            )
            session.add(AuditEvent(
                actor_role="Community Health Worker", action="Recorded screening observation",
                entity_type="screening", entity_id=str(screening.id), note=screening_type,
            ))
            rows = screening_service.all_screenings(session)
        return (
            f"Screening observation recorded (SC-{screening.id:04d}). It is pending clinician review and is "
            "not a diagnosis.",
            pd.DataFrame(rows, columns=ALL_COLUMNS),
        )
    except Exception as exc:  # noqa: BLE001
        return f"Could not record screening: {exc}", gr.skip()


def _review(screening_id, reviewer, outcome):
    if not screening_id:
        return "Choose a screening observation.", gr.skip(), gr.skip()
    if not reviewer or not reviewer.strip():
        return "Enter a reviewer alias.", gr.skip(), gr.skip()
    try:
        with session_scope() as session:
            screening = screening_service.review_screening(session, int(screening_id), reviewer.strip(), outcome)
            session.add(AuditEvent(
                actor_role="Medical Officer", action="Reviewed screening observation",
                entity_type="screening", entity_id=str(screening.id), note=outcome,
            ))
            queue = screening_service.review_queue(session)
            all_rows = screening_service.all_screenings(session)
        pending_choices = [(f"SC-{row['screening_id']:04d} — {row['participant']}", row["screening_id"]) for row in queue]
        return (
            f"Screening SC-{screening.id:04d} marked '{screening.review_status}'. Clinical confirmation remains "
            "the responsibility of the reviewing clinician.",
            pd.DataFrame(queue, columns=QUEUE_COLUMNS),
            gr.update(choices=pending_choices, value=pending_choices[0][1] if pending_choices else None),
        )
    except Exception as exc:  # noqa: BLE001
        return f"Could not review screening: {exc}", gr.skip(), gr.skip()


def build(demo) -> None:
    gr.HTML(section("Screening Operations"))
    gr.HTML(note(
        "Record screening observations and route them for clinician review. Screening observations are not "
        "diagnoses and must never be presented as confirmed conditions. Urgent symptoms require emergency care."
    ))
    controls = scope_controls()
    with gr.Row():
        btn = gr.Button("Refresh screening operations", variant="primary")
    kpis = gr.HTML()
    scope_note = gr.HTML()
    gr.HTML(section("Clinician review queue"))
    queue_table = gr.Dataframe(interactive=False, wrap=True, label="Pending clinician review")
    gr.HTML(section("All screening observations"))
    all_table = gr.Dataframe(interactive=False, wrap=True, label="Screening records")

    with gr.Row():
        with gr.Column():
            with gr.Accordion("Record a screening observation", open=True):
                participant = gr.Dropdown(label="Participant", choices=[])
                event = gr.Dropdown(label="Screening event", choices=[])
                stype = gr.Textbox(label="Screening type", placeholder="e.g. Blood pressure, Vision")
                observation = gr.Textbox(label="Observation note", lines=2,
                                         placeholder="Describe the demo observation without asserting diagnosis")
                result = gr.Dropdown(RESULT_CATEGORIES, value=RESULT_CATEGORIES[1], label="Result category")
                record_btn = gr.Button("Record observation", variant="primary")
                record_msg = gr.Markdown()
        with gr.Column():
            with gr.Accordion("Clinician review action", open=True):
                review_choice = gr.Dropdown(label="Pending observation", choices=[])
                reviewer = gr.Textbox(label="Reviewer alias", value="Dr. Rao (alias)")
                outcome = gr.Dropdown(["Reviewed", "Returned for clarification"], value="Reviewed", label="Outcome")
                review_btn = gr.Button("Record review")
                review_msg = gr.Markdown()

    outputs = [kpis, queue_table, all_table, event, participant, review_choice, scope_note]
    btn.click(refresh, inputs=list(controls), outputs=outputs)
    record_btn.click(
        _record, inputs=[participant, event, stype, observation, result],
        outputs=[record_msg, all_table],
    )
    review_btn.click(
        _review, inputs=[review_choice, reviewer, outcome],
        outputs=[review_msg, queue_table, review_choice],
    )
    demo.load(refresh, inputs=list(controls), outputs=outputs)
