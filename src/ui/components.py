"""Reusable UI rendering helpers and scope filter controls."""
from __future__ import annotations

import gradio as gr
import pandas as pd

from src.config import (
    DISTRICTS,
    FACILITY_ACTIVE_OPTIONS,
    FACILITY_CATEGORIES,
    MANDALS,
    MANDALS_BY_DISTRICT,
    STATES,
)


def kpi_cards(kpis: dict, definitions: list[tuple[str, str, str]]) -> str:
    cards = []
    for key, label, tone in definitions:
        value = kpis.get(key, 0)
        cards.append(
            f'<div class="bhd-kpi {tone}"><div class="v">{value}</div><div class="l">{label}</div></div>'
        )
    return f'<div class="bhd-kpi-grid">{"".join(cards)}</div>'


def alerts_html(alerts: list[dict]) -> str:
    if not alerts:
        return '<div class="bhd-note">No active operational alerts in the demo dataset.</div>'
    rows = []
    for alert in alerts:
        level = alert.get("level", "Info")
        rows.append(
            f'<div class="bhd-alert-row"><span class="bhd-pill {level}">{level}</span>'
            f'<span>{alert.get("text", "")}</span></div>'
        )
    return "".join(rows)


def note(text: str) -> str:
    return f'<div class="bhd-note">{text}</div>'


def section(text: str) -> str:
    return f'<div class="bhd-section">{text}</div>'


def emergency_html() -> str:
    return (
        '<div class="bhd-emergency">Emergency: if there are severe or immediately life-threatening symptoms '
        "(for example chest pain, severe bleeding, difficulty breathing or loss of consciousness), contact local "
        "emergency services or go to the nearest emergency department now. Do not wait for app navigation.</div>"
    )


def frame_or_empty(rows: list[dict], columns: list[str]) -> pd.DataFrame:
    if not rows:
        return pd.DataFrame(columns=columns)
    return pd.DataFrame(rows)


def safe_df(frame: pd.DataFrame | None) -> pd.DataFrame:
    if frame is None:
        return pd.DataFrame()
    return frame


def scope_controls(
    district_default: str = "All",
    category_default: str = "All",
    active_default: str = "All",
) -> tuple[gr.Dropdown, gr.Dropdown, gr.Dropdown, gr.Dropdown, gr.Dropdown]:
    """Render the standard State/District/Mandal/Category/Active filter row.

    Returns components in that order. Every screen passes their values into its
    refresh handler so filters stay local to the screen and do not conflict.
    """
    with gr.Row():
        state = gr.Dropdown(["All"] + STATES, value="All", label="State")
        district = gr.Dropdown(["All"] + DISTRICTS, value=district_default, label="District")
        mandal = gr.Dropdown(
            ["All"] + (MANDALS if district_default == "All" else MANDALS_BY_DISTRICT.get(district_default, [])),
            value="All",
            label="Mandal / block",
        )
        category = gr.Dropdown(["All"] + FACILITY_CATEGORIES, value=category_default, label="Facility category")
        active = gr.Dropdown(["All"] + FACILITY_ACTIVE_OPTIONS, value=active_default, label="Record status")

    def _mandals_for(value: str):
        values = MANDALS if value == "All" else MANDALS_BY_DISTRICT.get(value, [])
        return gr.update(choices=["All"] + values, value="All")

    district.change(_mandals_for, inputs=[district], outputs=[mandal])
    return state, district, mandal, category, active


def scope_args(controls: tuple) -> dict:
    state, district, mandal, category, active = controls
    return dict(state=state, district=district, mandal=mandal, category=category, active=active)


def detail_card(title: str, lines: list[str], footer: str = "") -> str:
    body = "".join(f"<div>{line}</div>" for line in lines)
    return (
        f'<div class="bhd-detail"><div class="t">{title}</div>{body}'
        f'<div class="f">{footer}</div></div>'
    )


def status_pill(status: str) -> str:
    return f'<span class="bhd-status">{status}</span>'
