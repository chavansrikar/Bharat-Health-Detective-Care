"""Reports and Analytics — operational summaries and CSV/zip exports."""
from __future__ import annotations

import tempfile
import zipfile
from datetime import date
from pathlib import Path

import gradio as gr
import pandas as pd

from src.database import session_scope
from src.services import reporting_service
from src.ui.components import kpi_cards, note, scope_controls, section

KPI_DEFS = [
    ("total_facilities", "Facilities", ""),
    ("referrals_total", "Referrals", ""),
    ("referral_completion_pct", "Referral completion", ""),
    ("followup_completion_pct", "Follow-up completion", ""),
    ("screening_review_pct", "Screening review", ""),
    ("utilization_pct", "Screening utilisation", ""),
    ("staffing_gaps", "Unfilled posts", "warn"),
    ("coverage_pct", "Catchment coverage", ""),
]

EXPORTS = [
    "Facilities",
    "Service utilisation",
    "Staffing gaps",
    "Workforce",
    "Screenings",
    "Referrals",
    "Diagnostics",
    "Campaigns",
    "Notifications",
    "Substance-use cases",
    "Employment applications",
    "Appointments",
]


def refresh(state, district, mandal, category, active):
    args = dict(state=state, district=district, mandal=mandal, category=category, active=active)
    with session_scope() as session:
        ids = reporting_service.scope_ids(session, **args)
        summary = reporting_service.overview_kpis(session, **args)
        util = reporting_service.utilization_df(session, ids)
        type_frame = reporting_service.facility_type_df(session, ids)
        staffing = reporting_service.staffing_gap_df(session, ids)
        referral_status = reporting_service.referral_status_df(session, ids)
    display = dict(summary)
    for key in ("referral_completion_pct", "followup_completion_pct", "screening_review_pct",
                "utilization_pct", "coverage_pct"):
        display[key] = f"{summary[key]:.1f}%"
    table = util[[
        "facility", "district", "mandal", "configured_capacity", "completed_sessions",
        "utilization_pct", "indicator",
    ]] if not util.empty else pd.DataFrame(
        columns=["facility", "district", "mandal", "configured_capacity", "completed_sessions",
                 "utilization_pct", "indicator"]
    )
    return (
        kpi_cards(display, KPI_DEFS),
        table,
        type_frame,
        referral_status,
        staffing,
        note(reporting_service.scope_label(state, district, mandal, category, active)),
    )


def _export(kind, state, district, mandal, category, active):
    args = dict(state=state, district=district, mandal=mandal, category=category, active=active)
    with session_scope() as session:
        ids = reporting_service.scope_ids(session, **args)
        csv_text = reporting_service.export_csv(session, kind, ids)
        util = reporting_service.utilization_df(session, ids)
        staffing = reporting_service.staffing_gap_df(session, ids)
    if not csv_text:
        return "No rows match the selected scope.", None, pd.DataFrame(), pd.DataFrame()
    folder = Path(tempfile.mkdtemp(prefix="bhd_export_"))
    path = folder / f"{kind.lower().replace(' ', '_')}_{date.today().isoformat()}.csv"
    path.write_text(csv_text, encoding="utf-8")
    return f"Generated {kind} export for the selected scope.", str(path), util, staffing


def _export_all(state, district, mandal, category, active):
    args = dict(state=state, district=district, mandal=mandal, category=category, active=active)
    folder = Path(tempfile.mkdtemp(prefix="bhd_export_all_"))
    archive = folder / f"bhd_reports_{date.today().isoformat()}.zip"
    written = 0
    with session_scope() as session:
        ids = reporting_service.scope_ids(session, **args)
        for kind in EXPORTS:
            try:
                text = reporting_service.export_csv(session, kind, ids)
            except Exception:
                continue
            if not text:
                continue
            name = kind.lower().replace(" ", "_") + ".csv"
            (folder / name).write_text(text, encoding="utf-8")
            written += 1
    if not written:
        return "No rows to export for this scope.", None
    with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as zip_file:
        for path in folder.glob("*.csv"):
            zip_file.write(path, arcname=path.name)
    return f"Generated one archive containing {written} CSV files for the selected scope.", str(archive)


def build(demo) -> None:
    gr.HTML(section("Reports and Analytics"))
    gr.HTML(note(
        "Operational report pack computed from the local demo database. Exports contain synthetic records only. "
        "CSV files are generated on demand; no real patient data is included or transmitted externally."
    ))
    controls = scope_controls()
    with gr.Row():
        btn = gr.Button("Refresh report summary", variant="primary")
    kpis = gr.HTML()
    scope_note = gr.HTML()
    gr.HTML(section("Service utilisation report"))
    util_table = gr.Dataframe(interactive=False, wrap=True, label="Facility utilisation")
    with gr.Row():
        type_table = gr.Dataframe(interactive=False, wrap=True, label="Facilities by type")
        referral_table = gr.Dataframe(interactive=False, wrap=True, label="Referrals by status")
    gr.HTML(section("Staffing gap report"))
    staffing_table = gr.Dataframe(interactive=False, wrap=True, label="Unfilled posts")

    gr.HTML(section("Exports"))
    with gr.Row():
        kind = gr.Dropdown(EXPORTS, value="Facilities", label="Dataset")
        export_btn = gr.Button("Generate CSV", variant="primary")
        export_all_btn = gr.Button("Generate all CSVs (zip)")
    export_msg = gr.Markdown()
    export_file = gr.File(label="Download generated report")
    with gr.Row():
        export_util = gr.Dataframe(interactive=False, wrap=True, label="Utilisation preview")
        export_staffing = gr.Dataframe(interactive=False, wrap=True, label="Staffing preview")

    outputs = [kpis, util_table, type_table, referral_table, staffing_table, scope_note]
    btn.click(refresh, inputs=list(controls), outputs=outputs)
    export_btn.click(
        _export, inputs=[kind] + list(controls),
        outputs=[export_msg, export_file, export_util, export_staffing],
    )
    export_all_btn.click(
        _export_all, inputs=list(controls), outputs=[export_msg, export_file]
    )
    demo.load(refresh, inputs=list(controls), outputs=outputs)
