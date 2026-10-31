"""Preventive Health Programmes — programme design and screening calendar."""
from __future__ import annotations

from datetime import date

import gradio as gr
import pandas as pd
import plotly.express as px

from src.database import session_scope
from src.models import AuditEvent
from src.services import facility_service, reporting_service, screening_service
from src.ui.components import kpi_cards, note, scope_controls, section

KPI_DEFS = [
    ("programmes", "Programmes", ""),
    ("screening_events", "Screening events", ""),
    ("screening_activities", "Screening observations", ""),
    ("pending_reviews", "Reviews pending", "warn"),
    ("screenings", "Participants screened", ""),
]

PROGRAMME_COLUMNS = ["name", "cohort", "eligibility", "start", "end", "status"]


def _programmes_df(session):
    rows = [
        {
            "name": p.name, "cohort": p.cohort_text, "eligibility": p.eligibility_notes,
            "start": p.start_date.isoformat(), "end": p.end_date.isoformat(), "status": p.status,
        }
        for p in screening_service.list_programmes(session)
    ]
    return pd.DataFrame(rows, columns=PROGRAMME_COLUMNS)


def refresh(state, district, mandal, category, active):
    args = dict(state=state, district=district, mandal=mandal, category=category, active=active)
    with session_scope() as session:
        ids = reporting_service.scope_ids(session, **args)
        kpis = reporting_service.overview_kpis(session, **args)
        programmes = screening_service.list_programmes(session)
        kpis["programmes"] = len(programmes)
        events = screening_service.list_events(session, facility_ids=ids)
        demand = reporting_service.service_demand_df(session, ids)
        programme_choices = screening_service.programme_choices(session)
        facility_choices = facility_service.facility_choices(session)
        programme_frame = _programmes_df(session)
    if demand.empty:
        chart = px.bar(title="No screening observations in scope")
    else:
        chart = px.bar(demand, x="observations", y="screening_type", orientation="h",
                       title="Screening observations by type")
        chart.update_layout(height=320, margin=dict(l=10, r=16, t=44, b=10), yaxis_title="", xaxis_title="Observations")
    return (
        kpi_cards(kpis, KPI_DEFS),
        programme_frame,
        pd.DataFrame(events, columns=["event_code", "event_name", "programme", "event_date", "status", "screenings"]),
        chart,
        gr.update(choices=programme_choices, value=programme_choices[0][1] if programme_choices else None),
        gr.update(choices=facility_choices, value=facility_choices[0][1] if facility_choices else None),
        note(reporting_service.scope_label(state, district, mandal, category, active)),
    )


def _parse_date(value: str):
    try:
        return date.fromisoformat(value.strip())
    except (AttributeError, ValueError):
        raise ValueError("Enter dates as YYYY-MM-DD")


def _create_programme(name, description, cohort, eligibility, start, end, status):
    try:
        start_date = _parse_date(start)
        end_date = _parse_date(end)
        with session_scope() as session:
            programme = screening_service.create_programme(
                session, name, description, cohort, eligibility, start_date, end_date, status
            )
            session.add(AuditEvent(
                actor_role="District Medical Officer", action="Created preventive programme",
                entity_type="programme", entity_id=str(programme.id), note=programme.name,
            ))
            frame = _programmes_df(session)
            choices = screening_service.programme_choices(session)
        return f"Programme '{programme.name}' created.", frame, gr.update(choices=choices, value=programme.id)
    except Exception as exc:  # noqa: BLE001
        return f"Could not create programme: {exc}", gr.skip(), gr.skip()


def _create_event(programme_id, facility_id, name, event_date, status):
    if not programme_id:
        return "Choose a programme.", gr.skip()
    try:
        when = _parse_date(event_date)
        with session_scope() as session:
            event = screening_service.create_event(
                session, int(programme_id), int(facility_id), name, when, status
            )
            session.add(AuditEvent(
                actor_role="Community Health Worker", action="Created screening event",
                entity_type="screening_event", entity_id=event.event_code, note=event.event_name,
            ))
            events = screening_service.list_events(session)
        return (
            f"Screening event {event.event_code} created for {event.event_date.isoformat()}.",
            pd.DataFrame(events, columns=["event_code", "event_name", "programme", "event_date", "status", "screenings"]),
        )
    except Exception as exc:  # noqa: BLE001
        return f"Could not create event: {exc}", gr.skip()


def build(demo) -> None:
    gr.HTML(section("Preventive Health Programmes"))
    gr.HTML(note(
        "Programme records describe preventive cohorts and screening opportunities. Eligibility text is demo "
        "guidance only and must be confirmed with the local clinical authority. Screening is not diagnosis."
    ))
    controls = scope_controls()
    with gr.Row():
        btn = gr.Button("Refresh programmes", variant="primary")
    kpis = gr.HTML()
    scope_note = gr.HTML()
    programme_table = gr.Dataframe(interactive=False, wrap=True, label="Preventive programmes")
    event_table = gr.Dataframe(interactive=False, wrap=True, label="Screening events")
    chart = gr.Plot(label="Screening demand by type")

    with gr.Row():
        with gr.Column():
            with gr.Accordion("Create a preventive programme", open=False):
                p_name = gr.Textbox(label="Programme name")
                p_desc = gr.Textbox(label="Description", lines=2)
                p_cohort = gr.Textbox(label="Cohort", placeholder="e.g. Adults 30+")
                p_elig = gr.Textbox(label="Eligibility notes", lines=2)
                with gr.Row():
                    p_start = gr.Textbox(value=date.today().isoformat(), label="Start (YYYY-MM-DD)")
                    p_end = gr.Textbox(value=date.today().replace(year=date.today().year + 1).isoformat(),
                                       label="End (YYYY-MM-DD)")
                p_status = gr.Dropdown(["Active", "Planned", "Completed"], value="Active", label="Status")
                p_create = gr.Button("Create programme", variant="primary")
                p_msg = gr.Markdown()
        with gr.Column():
            with gr.Accordion("Schedule a screening event", open=False):
                e_programme = gr.Dropdown(label="Programme", choices=[])
                e_facility = gr.Dropdown(label="Facility", choices=[])
                e_name = gr.Textbox(label="Event name")
                e_date = gr.Textbox(value=date.today().isoformat(), label="Event date (YYYY-MM-DD)")
                e_status = gr.Dropdown(["Planned", "Completed", "Cancelled"], value="Planned", label="Status")
                e_create = gr.Button("Create event", variant="primary")
                e_msg = gr.Markdown()

    outputs = [kpis, programme_table, event_table, chart, e_programme, e_facility, scope_note]
    btn.click(refresh, inputs=list(controls), outputs=outputs)
    p_create.click(
        _create_programme,
        inputs=[p_name, p_desc, p_cohort, p_elig, p_start, p_end, p_status],
        outputs=[p_msg, programme_table, e_programme],
    )
    e_create.click(
        _create_event, inputs=[e_programme, e_facility, e_name, e_date, e_status],
        outputs=[e_msg, event_table],
    )
    demo.load(refresh, inputs=list(controls), outputs=outputs)
