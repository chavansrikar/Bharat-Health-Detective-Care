"""Facility Locator and Mapping — schematic geographic search."""
from __future__ import annotations

import gradio as gr
import pandas as pd
import plotly.express as px

from src.config import (
    DISTRICTS,
    FACILITY_CATEGORIES,
    FACILITY_TYPES,
    MANDALS,
    MANDALS_BY_DISTRICT,
    OPERATING_STATUSES,
    STATES,
    VERIFICATION_STATUSES,
)
from src.database import session_scope
from src.services import facility_service
from src.ui.components import detail_card, note, section

COLUMNS = ["code", "name", "type", "category", "district", "mandal", "locality", "operating", "verification"]


def _map_figure(facilities):
    if not facilities:
        fig = px.scatter(title="No facilities match the current filters")
        fig.update_layout(height=400)
        return fig
    frame = pd.DataFrame([
        {
            "facility": f.name, "type": f.type, "lat": f.latitude, "lon": f.longitude,
            "mandal": f.mandal, "district": f.district, "status": f.operating_status,
            "active": "Active" if f.is_active else "Inactive",
        }
        for f in facilities
    ])
    frame = frame[frame["active"] == "Active"]
    if frame.empty:
        fig = px.scatter(title="No active facilities match the filters")
        fig.update_layout(height=400)
        return fig
    fig = px.scatter(
        frame, x="lon", y="lat", color="category" if "category" in frame else "type",
        hover_name="facility", hover_data=["mandal", "district", "status", "type"],
        title="Schematic facility map (approximate fictional coordinates)",
        symbol="type",
    )
    fig.update_traces(marker=dict(size=12, line=dict(width=1, color="white")))
    fig.update_layout(
        height=420, margin=dict(l=10, r=10, t=44, b=10),
        xaxis_title="Longitude (illustrative)", yaxis_title="Latitude (illustrative)",
        legend=dict(orientation="h", y=-0.25), paper_bgcolor="white",
    )
    return fig


def _detail(session, facility_id):
    facility = facility_service.get_facility(session, facility_id)
    if facility is None:
        return note("Select a facility from the results.")
    services = "".join(f'<span class="bhd-chip">{s.service_name}</span>' for s in facility.services) or "No services listed"
    return detail_card(
        facility.name,
        [
            f"{facility.type} · {facility_service.category_of(facility)} · {facility.ownership}",
            f"{facility.locality}, {facility.mandal}, {facility.district}",
            f"Operating status: <b>{facility.operating_status}</b> · Verification: <b>{facility.verification_status}</b>",
            f"Address: {facility.address_label or 'Not recorded'} · Phone placeholder: {facility.phone_placeholder}",
            f"Capacity notes: {facility.capacity_notes or 'Not recorded'}",
            f"<div style='margin-top:6px'><b>Services</b></div><div>{services}</div>",
        ],
        "Directory guidance only. Confirm service availability and timings directly with the facility. "
        "Emergency symptoms require immediate emergency care.",
    )


def search(text, ftype, category, state, district, mandal, service, verification, operating, active):
    args = dict(state=state, district=district, mandal=mandal, category=category, active=active)
    with session_scope() as session:
        facilities = facility_service.search_facilities(
            session, text=text or "", facility_type=ftype, service=service,
            verification=verification, operating=operating, **args,
        )
        rows = [
            {
                "code": f.code, "name": f.name, "type": f.type,
                "category": facility_service.category_of(f),
                "district": f.district, "mandal": f.mandal, "locality": f.locality,
                "operating": f.operating_status, "verification": f.verification_status,
            }
            for f in facilities
        ]
        choices = [(f"{f.code} — {f.name}", f.id) for f in facilities]
        detail_value = _detail(session, facilities[0].id) if facilities else note("No matching facilities.")
        service_choices = facility_service.facility_service_names(session)
    return (
        rows,
        gr.update(choices=choices, value=choices[0][1] if choices else None),
        detail_value,
        _map_figure(facilities),
        gr.update(choices=["All"] + service_choices, value=service),
    )


def _detail_handler(facility_id):
    if not facility_id:
        return note("Select a facility.")
    with session_scope() as session:
        return _detail(session, int(facility_id))


def build(demo) -> None:
    gr.HTML(section("Facility Locator and Mapping"))
    gr.HTML(note(
        "Search listed infrastructure by geography and service. Coordinates are approximate fictional demo "
        "values for a schematic map; this is not a live GIS or a guarantee of service availability."
    ))
    with gr.Row():
        text = gr.Textbox(label="Search name / locality / address", scale=2)
        ftype = gr.Dropdown(["All"] + FACILITY_TYPES, value="All", label="Facility type")
        category = gr.Dropdown(["All"] + FACILITY_CATEGORIES, value="All", label="Category")
    with gr.Row():
        state = gr.Dropdown(["All"] + STATES, value="All", label="State")
        district = gr.Dropdown(["All"] + DISTRICTS, value="All", label="District")
        mandal = gr.Dropdown(["All"] + MANDALS, value="All", label="Mandal")
        service = gr.Dropdown(["All"], value="All", label="Service")
    with gr.Row():
        verification = gr.Dropdown(["All"] + VERIFICATION_STATUSES, value="All", label="Verification")
        operating = gr.Dropdown(["All"] + OPERATING_STATUSES, value="All", label="Operating status")
        active = gr.Dropdown(["All", "Active", "Inactive"], value="Active", label="Record status")
        search_btn = gr.Button("Search facilities", variant="primary")
    results = gr.Dataframe(interactive=False, wrap=True, label="Matching facilities")
    map_plot = gr.Plot(label="Schematic facility map")
    detail_choice = gr.Dropdown(label="Facility detail", choices=[])
    detail_html = gr.HTML()

    def _district_changed(value):
        values = MANDALS if value == "All" else MANDALS_BY_DISTRICT.get(value, [])
        return gr.update(choices=["All"] + values, value="All")

    district.change(_district_changed, inputs=[district], outputs=[mandal])
    search_btn.click(
        search,
        inputs=[text, ftype, category, state, district, mandal, service, verification, operating, active],
        outputs=[results, detail_choice, detail_html, map_plot, service],
    )
    detail_choice.change(_detail_handler, inputs=[detail_choice], outputs=[detail_html])

    def initial():
        return search("", "All", "All", "All", "All", "All", "All", "All", "All", "Active")

    demo.load(initial, outputs=[results, detail_choice, detail_html, map_plot, service])
