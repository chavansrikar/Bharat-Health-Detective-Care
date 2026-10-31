"""Infrastructure Management — facility records, activation and service catalog."""
from __future__ import annotations

import gradio as gr

from src.config import (
    DISTRICTS,
    FACILITY_ACTIVE_OPTIONS,
    FACILITY_TYPES,
    MANDALS_BY_DISTRICT,
    OPERATING_STATUSES,
    OWNERSHIP_TYPES,
    SERVICE_OPTIONS,
    STATES,
    VERIFICATION_STATUSES,
)
from src.database import session_scope
from src.models import AuditEvent
from src.services import facility_service, reporting_service
from src.ui.components import detail_card, kpi_cards, note, scope_controls, section

KPI_DEFS = [
    ("total_facilities", "Facilities", ""),
    ("active_facilities", "Active", ""),
    ("inactive_facilities", "Inactive", "alert"),
    ("services", "Services listed", ""),
    ("pending_verification", "Pending verification", "warn"),
]

COLUMNS = ["code", "name", "type", "category", "district", "mandal", "ownership", "beds",
           "verification", "operating", "active", "services"]


def _refresh_table(session, text, ftype, args):
    facilities = facility_service.search_facilities(session, text=text or "", facility_type=ftype, **args)
    rows = [
        {
            "code": f.code, "name": f.name, "type": f.type,
            "category": facility_service.category_of(f), "district": f.district,
            "mandal": f.mandal, "ownership": f.ownership, "beds": f.beds,
            "verification": f.verification_status, "operating": f.operating_status,
            "active": "Active" if f.is_active else "Inactive",
            "services": ", ".join(s.service_name for s in f.services),
        }
        for f in facilities
    ]
    choices = [(f"{f.code} — {f.name}", f.id) for f in facilities]
    return rows, choices


def _detail(session, facility_id):
    facility = facility_service.get_facility(session, facility_id)
    if facility is None:
        return note("Select a facility to view its infrastructure record.")
    services = "".join(
        f'<span class="bhd-chip">{s.service_name} · cap {s.capacity_per_period}</span>' for s in facility.services
    ) or "<span class='bhd-chip'>No services listed</span>"
    return detail_card(
        facility.name,
        [
            f"{facility.type} · {facility_service.category_of(facility)} · {facility.ownership}",
            f"{facility.locality}, {facility.mandal}, {facility.district}, {facility.state}",
            f"Beds: <b>{facility.beds}</b> · Catchment population: <b>{facility.catchment_population:,}</b>",
            f"Operating: <b>{facility.operating_status}</b> · Verification: <b>{facility.verification_status}</b> · "
            f"Record: <b>{'Active' if facility.is_active else 'Inactive'}</b>",
            f"Capacity notes: {facility.capacity_notes or 'Not recorded'}",
            f"<div style='margin-top:6px'><b>Listed services</b></div><div>{services}</div>",
        ],
        "Demo record only. Confirm availability directly with the facility before relying on it.",
    )


def refresh(state, district, mandal, category, active, ftype, text):
    args = dict(state=state, district=district, mandal=mandal, category=category, active=active)
    with session_scope() as session:
        kpis = reporting_service.overview_kpis(session, **args)
        rows, choices = _refresh_table(session, text, ftype, args)
        detail_value = _detail(session, choices[0][1]) if choices else note("No facilities match the filters.")
    return (
        kpi_cards(kpis, KPI_DEFS),
        rows,
        gr.update(choices=choices, value=choices[0][1] if choices else None),
        detail_value,
        note(reporting_service.scope_label(state, district, mandal, category, active)),
    )


def _create_and_refresh(name, ftype, state, district, mandal, locality, address, ownership,
                        beds, catchment, verification, operating, capacity, services,
                        active_filter, category_filter, mandal_filter, text, ftype_filter):
    if not name or not name.strip():
        return "Enter a facility name.", gr.skip(), gr.skip(), gr.skip(), gr.skip()
    try:
        with session_scope() as session:
            facility = facility_service.create_facility(session, {
                "name": name, "type": ftype, "state": state, "district": district,
                "mandal": mandal, "locality": locality, "address_label": address,
                "ownership": ownership, "beds": beds, "catchment_population": catchment,
                "verification_status": verification, "operating_status": operating,
                "capacity_notes": capacity, "services": services or [],
            })
            session.add(AuditEvent(
                actor_role="District Administrator", action="Created facility record",
                entity_type="facility", entity_id=facility.code, note=facility.name,
            ))
        with session_scope() as session:
            rows, choices = _refresh_table(
                session, text, ftype_filter,
                dict(state=state, district=district, mandal=mandal_filter, category=category_filter,
                     active=active_filter),
            )
            detail_value = _detail(session, facility.id)
        return (
            f"Facility '{facility.name}' created as {facility.code}. Verification status is pending until reviewed.",
            rows, gr.update(choices=choices, value=facility.id), detail_value,
            note("Facility persisted to the local demo database."),
        )
    except Exception as exc:  # noqa: BLE001 - surfaced to user
        return f"Could not create facility: {exc}", gr.skip(), gr.skip(), gr.skip(), gr.skip()


def _update_status(facility_id, operating, verification, record_status):
    if not facility_id:
        return "Select a facility.", gr.skip()
    try:
        with session_scope() as session:
            facility_service.update_facility(session, int(facility_id), {
                "operating_status": operating,
                "verification_status": verification,
                "is_active": record_status == "Active",
            })
            session.add(AuditEvent(
                actor_role="District Administrator", action="Updated facility status",
                entity_type="facility", entity_id=str(facility_id),
                note=f"operating={operating}; verification={verification}; active={record_status}",
            ))
            value = _detail(session, int(facility_id))
        return "Facility status updated.", value
    except Exception as exc:  # noqa: BLE001
        return f"Could not update facility: {exc}", gr.skip()


def _add_service(facility_id, service_name, capacity, availability_note):
    if not facility_id:
        return "Select a facility.", gr.skip()
    try:
        with session_scope() as session:
            facility_service.add_service(
                session, int(facility_id), service_name, int(capacity or 0), availability_note or ""
            )
            session.add(AuditEvent(
                actor_role="Facility Administrator", action="Added service",
                entity_type="facility", entity_id=str(facility_id), note=service_name,
            ))
            value = _detail(session, int(facility_id))
        return f"Service '{service_name}' added to the facility catalog.", value
    except Exception as exc:  # noqa: BLE001
        return f"Could not add service: {exc}", gr.skip()


def build(demo) -> None:
    gr.HTML(section("Infrastructure Management"))
    gr.HTML(note(
        "Facility registry covering community, primary, secondary, tertiary and diagnostic infrastructure. "
        "Activation and verification are explicit demo fields; unverified records must not be treated as operational."
    ))
    controls = scope_controls()
    with gr.Row():
        ftype = gr.Dropdown(["All"] + FACILITY_TYPES, value="All", label="Facility type")
        text = gr.Textbox(label="Search name, locality or address", scale=2)
        refresh_btn = gr.Button("Apply filters", variant="primary")
    kpis = gr.HTML()
    scope_note = gr.HTML()
    table = gr.Dataframe(interactive=False, wrap=True, label="Facility infrastructure records")

    with gr.Row():
        with gr.Column(scale=3):
            detail_choice = gr.Dropdown(label="Facility detail", choices=[])
            detail_html = gr.HTML()
        with gr.Column(scale=2):
            gr.HTML(section("Update operating status"))
            gr.HTML(note("Changes apply to the demo record and are written to the activity log."))
            op_status = gr.Dropdown(OPERATING_STATUSES, value="Operational", label="Operating status")
            ver_status = gr.Dropdown(VERIFICATION_STATUSES, value="Verified", label="Verification status")
            rec_status = gr.Dropdown(FACILITY_ACTIVE_OPTIONS, value="Active", label="Record status")
            update_btn = gr.Button("Update facility")
            status_msg = gr.Markdown()

    with gr.Accordion("Add a facility", open=False):
        with gr.Row():
            name = gr.Textbox(label="Facility name")
            ntype = gr.Dropdown(FACILITY_TYPES, value="PHC", label="Facility type")
            ownership = gr.Dropdown(OWNERSHIP_TYPES, value="Government", label="Ownership")
        with gr.Row():
            nstate = gr.Dropdown(STATES, value=STATES[0], label="State")
            ndistrict = gr.Dropdown(DISTRICTS, value=DISTRICTS[0], label="District")
            nmandal = gr.Dropdown(MANDALS_BY_DISTRICT[DISTRICTS[0]], value=MANDALS_BY_DISTRICT[DISTRICTS[0]][0],
                                  label="Mandal")
        with gr.Row():
            locality = gr.Textbox(label="Village / locality")
            address = gr.Textbox(label="Address label")
        with gr.Row():
            beds = gr.Number(value=0, precision=0, label="Beds")
            catchment = gr.Number(value=0, precision=0, label="Catchment population")
            nverif = gr.Dropdown(VERIFICATION_STATUSES, value="Pending verification", label="Verification")
            noper = gr.Dropdown(OPERATING_STATUSES, value="Operational", label="Operating status")
        capacity = gr.Textbox(label="Capacity notes", placeholder="e.g. 6 beds; weekday OPD; lab")
        services = gr.Dropdown(SERVICE_OPTIONS, multiselect=True, label="Services to list")
        create_btn = gr.Button("Create facility record", variant="primary")
        create_msg = gr.Markdown()

    def _ndistrict_changed(value):
        values = MANDALS_BY_DISTRICT.get(value, [])
        return gr.update(choices=values, value=values[0] if values else None)

    ndistrict.change(_ndistrict_changed, inputs=[ndistrict], outputs=[nmandal])

    with gr.Accordion("Add a service to a facility", open=False):
        service_facility = gr.Dropdown(label="Facility", choices=[])
        with gr.Row():
            service_name = gr.Dropdown(SERVICE_OPTIONS, value=SERVICE_OPTIONS[0], label="Service")
            service_capacity = gr.Number(value=20, precision=0, label="Capacity / period")
        availability_note = gr.Textbox(label="Availability note", value="Confirm by phone")
        add_service_btn = gr.Button("Add service")
        service_msg = gr.Markdown()

    refresh_outputs = [kpis, table, detail_choice, detail_html, scope_note]
    refresh_btn.click(refresh, inputs=list(controls) + [ftype, text], outputs=refresh_outputs)
    detail_choice.change(
        lambda fid: (_detail_for(fid)), inputs=[detail_choice], outputs=[detail_html]
    )
    update_btn.click(
        _update_status, inputs=[detail_choice, op_status, ver_status, rec_status],
        outputs=[status_msg, detail_html],
    )
    create_btn.click(
        _create_and_refresh,
        inputs=[name, ntype, nstate, ndistrict, nmandal, locality, address, ownership,
                beds, catchment, nverif, noper, capacity, services,
                controls[4], controls[3], controls[2], text, ftype],
        outputs=[create_msg, table, detail_choice, detail_html, scope_note],
    )
    add_service_btn.click(
        _add_service,
        inputs=[service_facility, service_name, service_capacity, availability_note],
        outputs=[service_msg, detail_html],
    )

    def initial():
        result = refresh(*[c.value for c in controls], "All", "")
        with session_scope() as session:
            choices = facility_service.facility_choices(session)
        return result + (gr.update(choices=choices, value=choices[0][1] if choices else None),)

    demo.load(initial, outputs=refresh_outputs + [service_facility])


def _detail_for(facility_id):
    if not facility_id:
        return note("Select a facility.")
    with session_scope() as session:
        return _detail(session, int(facility_id))
