"""Facility Utilization Analytics — capacity, activity and operational gaps."""
from __future__ import annotations

import gradio as gr
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from src.database import session_scope
from src.models import Facility, Service, Staff
from src.services import reporting_service
from src.ui.components import kpi_cards, note, scope_controls, section

KPI_DEFS = [
    ("facilities", "Facilities in scope", ""),
    ("utilization_pct", "Avg. screening utilisation", ""),
    ("screening_activities", "Screening observations", ""),
    ("staff_available", "Staff available", ""),
    ("staffing_gaps", "Unfilled posts", "warn"),
]


def _empty(message: str) -> go.Figure:
    fig = go.Figure()
    fig.add_annotation(text=message, showarrow=False, font=dict(size=13, color="#64748b"))
    fig.update_xaxes(visible=False)
    fig.update_yaxes(visible=False)
    fig.update_layout(height=330, margin=dict(l=10, r=10, t=40, b=10))
    return fig


def _gaps(session, ids):
    facilities = session.query(Facility).filter(Facility.id.in_(ids)).all() if ids else []
    rows = []
    for facility in facilities:
        roles = {
            row.role for row in session.query(Staff).filter(
                Staff.facility_id == facility.id,
                Staff.availability.in_(["Available", "On duty"]),
            ).all()
        }
        services = {s.service_name for s in facility.services if s.active}
        missing = []
        if "Medical Officer" not in roles and "Specialist Doctor" not in roles:
            missing.append("No doctor currently available")
        if not ({"Laboratory diagnostics", "Imaging / radiology"} & services):
            missing.append("No listed diagnostic service")
        if not facility.is_active:
            missing.append("Record marked inactive")
        if missing:
            rows.append({
                "facility": facility.name, "district": facility.district,
                "mandal": facility.mandal, "gaps": "; ".join(missing),
            })
    return pd.DataFrame(rows, columns=["facility", "district", "mandal", "gaps"])


def refresh(state, district, mandal, category, active):
    args = dict(state=state, district=district, mandal=mandal, category=category, active=active)
    with session_scope() as session:
        ids = reporting_service.scope_ids(session, **args)
        kpis = reporting_service.overview_kpis(session, **args)
        frame = reporting_service.utilization_df(session, ids)
        gaps = _gaps(session, ids)
    display = dict(kpis)
    display["utilization_pct"] = f"{kpis['utilization_pct']:.1f}%"
    if frame.empty:
        low = pd.DataFrame(columns=["facility", "utilization_pct", "completed_sessions"])
        idle = pd.DataFrame(columns=["facility", "configured_capacity", "district", "mandal"])
        figure = _empty("No facilities in the selected scope")
    else:
        active_rows = frame[frame["completed_sessions"] > 0].sort_values("utilization_pct", ascending=False).head(12)
        figure = px.bar(
            active_rows, x="facility", y="utilization_pct", color="indicator",
            hover_data=["completed_sessions", "configured_capacity"],
            title="Screening utilisation by facility (demo formula)",
        )
        figure.update_layout(height=340, margin=dict(l=10, r=16, t=44, b=100), xaxis_title="", yaxis_title="%")
        figure.update_xaxes(tickangle=-25)
        low = frame[(frame["completed_sessions"] > 0) & (frame["utilization_pct"] < 40)][
            ["facility", "utilization_pct", "completed_sessions", "configured_capacity"]
        ].sort_values("utilization_pct")
        idle = frame[(frame["configured_capacity"] > 0) & (frame["completed_sessions"] == 0)][
            ["facility", "configured_capacity", "district", "mandal"]
        ]
    total = pd.DataFrame(columns=["facility", "type", "district", "mandal", "configured_capacity", "completed_sessions", "utilization_pct", "indicator"])
    if not frame.empty:
        total = frame[[
            "facility", "type", "district", "mandal", "configured_capacity",
            "completed_sessions", "utilization_pct", "indicator",
        ]].sort_values("utilization_pct", ascending=False)
    return (
        kpi_cards(display, KPI_DEFS),
        total,
        figure,
        low,
        idle,
        gaps,
        note(reporting_service.scope_label(state, district, mandal, category, active)),
    )


def build(demo) -> None:
    gr.HTML(section("Facility Utilization Analytics"))
    gr.HTML(note(
        "Documented demo indicator: attendance at completed screening events ÷ configured preventive-service "
        "capacity for the same facility. This is an operational planning view, not a clinical quality score. "
        "Zero activity does not imply poor performance; it may reflect missing records or a planned-only calendar."
    ))
    controls = scope_controls()
    with gr.Row():
        btn = gr.Button("Refresh analytics", variant="primary")
    kpis = gr.HTML()
    scope_note = gr.HTML()
    table = gr.Dataframe(interactive=False, wrap=True, label="Capacity vs activity")
    chart = gr.Plot(label="Utilisation by facility")
    with gr.Row():
        low = gr.Dataframe(interactive=False, wrap=True, label="Low-utilisation facilities (<40%)")
        idle = gr.Dataframe(interactive=False, wrap=True, label="No completed screening activity")
    gaps = gr.Dataframe(interactive=False, wrap=True, label="Operational gaps")
    outputs = [kpis, table, chart, low, idle, gaps, scope_note]
    btn.click(refresh, inputs=list(controls), outputs=outputs)
    demo.load(refresh, inputs=list(controls), outputs=outputs)
