"""Healthcare Overview — enterprise operations command centre."""
from __future__ import annotations

import gradio as gr
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from src.database import session_scope
from src.services import facility_service, reporting_service
from src.ui.components import alerts_html, kpi_cards, note, scope_controls, section

KPI_DEFS = [
    ("total_facilities", "Facilities in scope", ""),
    ("active_facilities", "Active facilities", ""),
    ("inactive_facilities", "Inactive records", "alert"),
    ("utilization_pct", "Avg. screening utilisation", ""),
    ("services", "Services listed", ""),
    ("staff_available", "Staff available", ""),
    ("staffing_gaps", "Unfilled posts", "warn"),
    ("screening_activities", "Screening observations", ""),
    ("pending_reports", "Reports pending", "warn"),
    ("referrals_open", "Open referrals", ""),
    ("followup_completion_pct", "Follow-up completion", ""),
    ("coverage_pct", "Catchment coverage", ""),
]

NAVY = "#0b2545"
TEAL = "#0f766e"
STATUS_COLORS = {
    "Draft": "#94a3b8", "Sent": "#38bdf8", "Accepted": "#0ea5e9", "Scheduled": "#6366f1",
    "Attended": "#14b8a6", "Completed": "#16a34a", "Returned for clarification": "#f59e0b",
    "Cancelled": "#dc2626",
}


def empty_figure(message: str) -> go.Figure:
    fig = go.Figure()
    fig.add_annotation(text=message, showarrow=False, font=dict(size=13, color="#64748b"))
    fig.update_xaxes(visible=False)
    fig.update_yaxes(visible=False)
    fig.update_layout(height=280, margin=dict(l=10, r=10, t=40, b=10), paper_bgcolor="white")
    return fig


def _bar(df: pd.DataFrame, x: str, y: str, title: str, color: str | None = None, horizontal: bool = True) -> go.Figure:
    if df.empty:
        return empty_figure("No matching demo records")
    if horizontal:
        fig = px.bar(df, x=x, y=y, orientation="h", title=title, color=color,
                     color_discrete_sequence=["#0f766e"])
        fig.update_layout(yaxis_title="", xaxis_title="")
    else:
        fig = px.bar(df, x=x, y=y, title=title, color=color,
                     color_discrete_sequence=["#0f766e"])
        fig.update_layout(xaxis_title="", yaxis_title="")
    fig.update_layout(height=290, margin=dict(l=10, r=16, t=44, b=20), paper_bgcolor="white")
    return fig


def _facility_type_fig(ids, kpis):
    with session_scope() as session:
        frame = reporting_service.facility_type_df(session, ids)
    return _bar(frame, "count", "type", "Facilities by type")


def _referral_fig(ids):
    with session_scope() as session:
        frame = reporting_service.referral_status_df(session, ids)
    if frame.empty:
        return empty_figure("No referral records in scope")
    fig = px.pie(frame, names="status", values="count", title="Referral status distribution",
                 hole=0.58, color="status", color_discrete_map=STATUS_COLORS)
    fig.update_layout(height=290, margin=dict(l=10, r=10, t=44, b=10), paper_bgcolor="white")
    fig.update_traces(textposition="inside", textinfo="percent")
    return fig


def _screening_fig(ids):
    with session_scope() as session:
        frame = reporting_service.screening_by_month_df(session, ids)
    if frame.empty:
        return empty_figure("No screening activity in scope")
    fig = px.line(frame, x="month", y="screenings", markers=True, title="Screening observations by month")
    fig.update_layout(height=290, margin=dict(l=10, r=16, t=44, b=10), xaxis_title="", yaxis_title="Observations")
    fig.update_traces(line_color=NAVY, marker_color=TEAL)
    return fig


def _utilization_fig(ids):
    with session_scope() as session:
        frame = reporting_service.utilization_df(session, ids)
    active = frame[frame["completed_sessions"] > 0].sort_values("utilization_pct", ascending=False).head(10)
    if active.empty:
        return empty_figure("No completed screening activity in scope")
    fig = px.bar(
        active, x="facility", y="utilization_pct", color="indicator",
        hover_data=["completed_sessions", "configured_capacity"],
        title="Screening utilisation by facility (demo formula)",
    )
    fig.update_layout(height=290, margin=dict(l=10, r=16, t=44, b=90), xaxis_title="", yaxis_title="%",
                      paper_bgcolor="white")
    fig.update_xaxes(tickangle=-25)
    return fig


def _access_gaps(ids, args):
    with session_scope() as session:
        rows = reporting_service.access_gap_rows(session, **args)
    gaps = [r for r in rows if r["status"] != "Covered"]
    return pd.DataFrame(gaps, columns=["district", "mandal", "active_facilities", "primary_or_higher", "status"])


def refresh(state, district, mandal, category, active):
    args = dict(state=state, district=district, mandal=mandal, category=category, active=active)
    with session_scope() as session:
        ids = reporting_service.scope_ids(session, **args)
        kpis = reporting_service.overview_kpis(session, **args)
        alerts = reporting_service.operational_alerts(session, **args)
    display = dict(kpis)
    display["utilization_pct"] = f"{kpis['utilization_pct']:.1f}%"
    display["followup_completion_pct"] = f"{kpis['followup_completion_pct']:.1f}%"
    display["coverage_pct"] = f"{kpis['coverage_pct']:.1f}%"
    gaps = _access_gaps(ids, args)
    return (
        kpi_cards(display, KPI_DEFS),
        alerts_html(alerts),
        _facility_type_fig(ids, kpis),
        _referral_fig(ids),
        _screening_fig(ids),
        _utilization_fig(ids),
        gaps,
        note(reporting_service.scope_label(state, district, mandal, category, active)),
    )


def build(demo) -> None:
    gr.HTML(section("Healthcare Overview"))
    gr.HTML(note(
        "Live operational view across facilities, workforce, prevention, diagnostics and referral coordination. "
        "All metrics are computed from fictional demo data; utilisation is a planning indicator, not a clinical score."
    ))
    controls = scope_controls()
    with gr.Row():
        refresh_btn = gr.Button("Refresh overview", variant="primary")
    scope_note = gr.HTML()
    kpis = gr.HTML()
    gr.HTML(section("Operational alerts"))
    alerts = gr.HTML()
    with gr.Row():
        f1 = gr.Plot(label="Facilities by type")
        f2 = gr.Plot(label="Referral status")
    with gr.Row():
        f3 = gr.Plot(label="Screening activity")
        f4 = gr.Plot(label="Screening utilisation")
    gr.HTML(section("Access gaps by mandal"))
    gr.HTML(note(
        "A demo coverage view: mandals without an active primary-care or higher facility are highlighted. "
        "This does not measure real travel time, population need or service quality."
    ))
    gaps = gr.Dataframe(interactive=False, wrap=True, label="Mandals needing review")
    outputs = [kpis, alerts, f1, f2, f3, f4, gaps, scope_note]
    refresh_btn.click(refresh, inputs=list(controls), outputs=outputs)
    demo.load(refresh, inputs=list(controls), outputs=outputs)
