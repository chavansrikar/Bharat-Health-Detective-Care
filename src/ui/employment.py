"""Healthcare Employment — vacancies, applications and recruitment status."""
from __future__ import annotations

import gradio as gr
import pandas as pd

from src.config import APPLICATION_STATUSES, WORKFORCE_ROLES
from src.database import session_scope
from src.models import AuditEvent
from src.services import facility_service, reporting_service, workforce_service
from src.ui.components import kpi_cards, note, scope_controls, section

KPI_DEFS = [
    ("applications_received", "Applications", ""),
    ("applications_pending", "In review", "warn"),
    ("hired", "Offers issued", ""),
    ("open_vacancies", "Open vacancies", "warn"),
    ("vacancy_gap", "Unfilled posts", "alert"),
]

APP_COLUMNS = ["application_code", "applicant", "role", "facility", "qualification",
               "experience_years", "status", "applied_at"]
VACANCY_COLUMNS = ["vacancy_code", "facility", "role", "required", "filled", "gap", "status", "priority"]


def refresh(state, district, mandal, category, active, status, role):
    args = dict(state=state, district=district, mandal=mandal, category=category, active=active)
    with session_scope() as session:
        ids = reporting_service.scope_ids(session, **args)
        summary = workforce_service.workforce_summary(session, ids)
        apps = workforce_service.list_applications(session, ids, status=status, role=role)
        vacancies = workforce_service.list_vacancies(session, ids)
        choices = [(a["application_code"] + " — " + a["applicant"], a["application_id"]) for a in apps]
        facility_choices = facility_service.facility_choices(session)
    return (
        kpi_cards(summary, KPI_DEFS),
        pd.DataFrame(apps, columns=APP_COLUMNS),
        pd.DataFrame(vacancies, columns=VACANCY_COLUMNS),
        gr.update(choices=choices, value=choices[0][1] if choices else None),
        gr.update(choices=facility_choices, value=facility_choices[0][1] if facility_choices else None),
        note(reporting_service.scope_label(state, district, mandal, category, active)),
    )


def _apply(alias, role, facility_id, qualification, experience, notes):
    try:
        with session_scope() as session:
            application = workforce_service.create_application(
                session, alias, role, int(facility_id) if facility_id else None,
                qualification, int(experience or 0), notes or "",
            )
            session.add(AuditEvent(
                actor_role="Applicant (demo)", action="Submitted employment application",
                entity_type="application", entity_id=application.application_code,
                note=application.role,
            ))
            apps = workforce_service.list_applications(session)
            choices = [(a["application_code"] + " — " + a["applicant"], a["application_id"]) for a in apps]
        return (
            f"Application {application.application_code} received. This is a demo record; no real recruitment "
            "decision is made.",
            pd.DataFrame(apps, columns=APP_COLUMNS),
            gr.update(choices=choices, value=application.id),
        )
    except Exception as exc:  # noqa: BLE001
        return f"Could not submit application: {exc}", gr.skip(), gr.skip()


def _update(application_id, status, actor):
    if not application_id:
        return "Select an application."
    try:
        with session_scope() as session:
            application = workforce_service.update_application_status(session, int(application_id), status)
            session.add(AuditEvent(
                actor_role=actor or "HR reviewer", action=f"Application status → {status}",
                entity_type="application", entity_id=application.application_code,
                note=application.applicant_alias,
            ))
        return f"Application {application.application_code} set to '{application.status}'."
    except Exception as exc:  # noqa: BLE001
        return f"Could not update application: {exc}"


def build(demo) -> None:
    gr.HTML(section("Healthcare Employment"))
    gr.HTML(note(
        "Recruitment register linking facility vacancies to demo applications. Applicant aliases are synthetic. "
        "This module supports administrative tracking only and does not make automated hiring decisions."
    ))
    controls = scope_controls(active_default="Active")
    with gr.Row():
        status = gr.Dropdown(["All"] + APPLICATION_STATUSES, value="All", label="Application status")
        role = gr.Dropdown(["All"] + WORKFORCE_ROLES, value="All", label="Role")
        btn = gr.Button("Apply employment filters", variant="primary")
    kpis = gr.HTML()
    scope_note = gr.HTML()
    gr.HTML(section("Applications"))
    app_table = gr.Dataframe(interactive=False, wrap=True, label="Healthcare employment applications")
    gr.HTML(section("Open vacancy context"))
    vacancy_table = gr.Dataframe(interactive=False, wrap=True, label="Vacancies in scope")

    with gr.Row():
        with gr.Column(scale=3):
            with gr.Accordion("Submit a demo application", open=False):
                alias = gr.Textbox(label="Applicant alias", placeholder="Applicant A11 (alias)")
                app_role = gr.Dropdown(WORKFORCE_ROLES, value=WORKFORCE_ROLES[0], label="Role")
                facility = gr.Dropdown(label="Preferred facility", choices=[])
                qualification = gr.Textbox(label="Qualification", value="Demo qualification")
                experience = gr.Number(value=0, precision=0, label="Experience (years)")
                notes = gr.Textbox(label="Notes", lines=2)
                apply_btn = gr.Button("Submit application", variant="primary")
                apply_msg = gr.Markdown()
        with gr.Column(scale=2):
            gr.HTML(section("Review application"))
            choice = gr.Dropdown(label="Application", choices=[])
            new_status = gr.Dropdown(APPLICATION_STATUSES, value="Shortlisted", label="New status")
            reviewer = gr.Textbox(label="Reviewer alias", value="HR reviewer (alias)")
            update_btn = gr.Button("Update application status")
            update_msg = gr.Markdown()

    outputs = [kpis, app_table, vacancy_table, choice, facility, scope_note]
    btn.click(refresh, inputs=list(controls) + [status, role], outputs=outputs)
    apply_btn.click(
        _apply, inputs=[alias, app_role, facility, qualification, experience, notes],
        outputs=[apply_msg, app_table, choice],
    )
    update_btn.click(_update, inputs=[choice, new_status, reviewer], outputs=[update_msg])
    demo.load(refresh, inputs=list(controls) + [status, role], outputs=outputs)
