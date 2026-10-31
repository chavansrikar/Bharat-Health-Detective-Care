"""Medical Workforce Management — staff availability and vacancy control."""
from __future__ import annotations

import gradio as gr
import pandas as pd
import plotly.express as px

from src.config import STAFF_AVAILABILITY, VACANCY_PRIORITIES, VACANCY_STATUSES, WORKFORCE_ROLES
from src.database import session_scope
from src.models import AuditEvent
from src.services import facility_service, reporting_service, workforce_service
from src.ui.components import kpi_cards, note, scope_controls, section

KPI_DEFS = [
    ("staff_total", "Staff in scope", ""),
    ("available", "Available", ""),
    ("on_leave", "On leave", "warn"),
    ("open_vacancies", "Open vacancies", "warn"),
    ("vacancy_gap", "Unfilled posts", "alert"),
    ("applications_pending", "Applications pending", ""),
]

STAFF_COLUMNS = ["staff_code", "name", "role", "qualification", "facility", "skills",
                 "availability", "shift", "employment_type", "verification"]
VACANCY_COLUMNS = ["vacancy_code", "facility", "role", "required", "filled", "gap", "status", "priority", "notes"]


def _refresh(session, args, role, availability, text):
    ids = reporting_service.scope_ids(session, **args)
    summary = workforce_service.workforce_summary(session, ids)
    staff = workforce_service.list_staff(session, ids, role=role, availability=availability, text=text or "")
    vacancies = workforce_service.list_vacancies(session, ids, status="All", priority="All", role="All")
    gaps = workforce_service.facility_staffing_rows(session, ids)
    gap_rows = [g for g in gaps if g["vacancy_gap"] > 0]
    return summary, staff, vacancies, pd.DataFrame(gap_rows, columns=["facility", "district", "mandal", "staff", "vacancy_gap", "status"])


def refresh(state, district, mandal, category, active, role, availability, text):
    args = dict(state=state, district=district, mandal=mandal, category=category, active=active)
    with session_scope() as session:
        summary, staff, vacancies, gaps = _refresh(session, args, role, availability, text)
        facility_choices = facility_service.facility_choices(session)
        vacancy_choices = workforce_service.vacancy_choices(session)
        ids = reporting_service.scope_ids(session, **args)
        gap_frame = pd.DataFrame(
            [g for g in workforce_service.facility_staffing_rows(session, ids) if g["vacancy_gap"] > 0]
        )
    if gap_frame.empty:
        chart = px.bar(title="No unfilled posts in scope")
    else:
        top = gap_frame.sort_values("vacancy_gap", ascending=False).head(12)
        chart = px.bar(top, x="facility", y="vacancy_gap", title="Unfilled posts by facility",
                       color="vacancy_gap", color_continuous_scale="Teal")
        chart.update_layout(height=320, margin=dict(l=10, r=16, t=44, b=90), xaxis_title="", yaxis_title="Gap")
        chart.update_xaxes(tickangle=-25)
    return (
        kpi_cards(summary, KPI_DEFS),
        pd.DataFrame(staff, columns=STAFF_COLUMNS),
        pd.DataFrame(vacancies, columns=VACANCY_COLUMNS),
        pd.DataFrame(gaps, columns=["facility", "district", "mandal", "staff", "vacancy_gap", "status"]),
        chart,
        gr.update(choices=facility_choices, value=facility_choices[0][1] if facility_choices else None),
        gr.update(choices=vacancy_choices, value=vacancy_choices[0][1] if vacancy_choices else None),
        note(reporting_service.scope_label(state, district, mandal, category, active)),
    )


def _create_vacancy(facility_id, role, required, priority, notes):
    if not facility_id:
        return "Choose a facility first.", gr.skip(), gr.skip()
    try:
        with session_scope() as session:
            vacancy = workforce_service.create_vacancy(
                session, int(facility_id), role, int(required or 1), priority, notes or ""
            )
            session.add(AuditEvent(
                actor_role="Facility Administrator", action="Created staffing vacancy",
                entity_type="vacancy", entity_id=vacancy.vacancy_code,
                note=f"{role} × {required}",
            ))
            choices = workforce_service.vacancy_choices(session)
            vacancies = workforce_service.list_vacancies(session)
        return (
            f"Vacancy {vacancy.vacancy_code} created for {role}.",
            pd.DataFrame(vacancies, columns=VACANCY_COLUMNS),
            gr.update(choices=choices, value=vacancy.id),
        )
    except Exception as exc:  # noqa: BLE001
        return f"Could not create vacancy: {exc}", gr.skip(), gr.skip()


def _update_vacancy(vacancy_id, filled, status):
    if not vacancy_id:
        return "Choose a vacancy.", gr.skip()
    try:
        with session_scope() as session:
            vacancy = workforce_service.update_vacancy(
                session, int(vacancy_id),
                filled_count=int(filled) if filled is not None else None,
                status=status or None,
            )
            session.add(AuditEvent(
                actor_role="Facility Administrator", action="Updated vacancy",
                entity_type="vacancy", entity_id=vacancy.vacancy_code,
                note=f"filled={vacancy.filled_count}/{vacancy.required_count}; status={vacancy.status}",
            ))
            vacancies = workforce_service.list_vacancies(session)
        return "Vacancy updated.", pd.DataFrame(vacancies, columns=VACANCY_COLUMNS)
    except Exception as exc:  # noqa: BLE001
        return f"Could not update vacancy: {exc}", gr.skip()


def build(demo) -> None:
    gr.HTML(section("Medical Workforce Management"))
    gr.HTML(note(
        "Workforce records are synthetic. Availability reflects the demo shift roster, not live attendance. "
        "Unfilled posts are calculated from configured vacancies and must be verified before real deployment decisions."
    ))
    controls = scope_controls()
    with gr.Row():
        role = gr.Dropdown(["All"] + WORKFORCE_ROLES, value="All", label="Role")
        availability = gr.Dropdown(["All"] + STAFF_AVAILABILITY, value="All", label="Availability")
        text = gr.Textbox(label="Search staff name or skills", scale=2)
        btn = gr.Button("Apply workforce filters", variant="primary")
    kpis = gr.HTML()
    scope_note = gr.HTML()
    gr.HTML(section("Staff roster"))
    staff_table = gr.Dataframe(interactive=False, wrap=True, label="Staff availability")
    gr.HTML(section("Staffing gaps"))
    with gr.Row():
        gap_table = gr.Dataframe(interactive=False, wrap=True, label="Facilities with unfilled posts")
        gap_chart = gr.Plot(label="Unfilled posts")
    gr.HTML(section("Vacancy control"))
    vacancy_table = gr.Dataframe(interactive=False, wrap=True, label="Configured vacancies")
    with gr.Row():
        with gr.Column():
            gr.HTML(note("Create a vacancy against a listed facility."))
            v_facility = gr.Dropdown(label="Facility", choices=[])
            v_role = gr.Dropdown(WORKFORCE_ROLES, value=WORKFORCE_ROLES[0], label="Role")
            v_required = gr.Number(value=1, precision=0, label="Required count")
            v_priority = gr.Dropdown(VACANCY_PRIORITIES, value="Routine", label="Priority")
            v_notes = gr.Textbox(label="Notes", placeholder="e.g. emergency cover")
            v_create = gr.Button("Create vacancy", variant="primary")
            v_msg = gr.Markdown()
        with gr.Column():
            gr.HTML(note("Update filled count or close a vacancy after review."))
            v_choice = gr.Dropdown(label="Vacancy", choices=[])
            v_filled = gr.Number(value=0, precision=0, label="Filled count")
            v_status = gr.Dropdown(VACANCY_STATUSES, value="Partially filled", label="Status")
            v_update = gr.Button("Update vacancy")
            v_update_msg = gr.Markdown()

    outputs = [kpis, staff_table, vacancy_table, gap_table, gap_chart, v_facility, v_choice, scope_note]
    btn.click(refresh, inputs=list(controls) + [role, availability, text], outputs=outputs)
    v_create.click(
        _create_vacancy, inputs=[v_facility, v_role, v_required, v_priority, v_notes],
        outputs=[v_msg, vacancy_table, v_choice],
    )
    v_update.click(_update_vacancy, inputs=[v_choice, v_filled, v_status], outputs=[v_update_msg, vacancy_table])
    demo.load(refresh, inputs=list(controls) + [role, availability, text], outputs=outputs)
