"""Bharat Health Detective Care — healthcare operations platform entry point.

Run locally:  python app.py
Hugging Face Spaces: this file is the app entry point on port 7860.
"""
from __future__ import annotations

import os

import gradio as gr

try:
    import spaces
except ImportError:
    spaces = None

from src.config import APP_NAME, DEMO_ROLES
from src.database import init_db, session_scope
from src.seed import seed_database
from src.ui import (
    admin,
    campaigns,
    citizen,
    dashboard,
    diagnostics,
    employment,
    infrastructure,
    locator,
    notifications,
    prevention,
    referrals,
    registry,
    reports,
    screening_ops,
    substance,
    theme,
    utilization,
    workforce,
)
from src.ui.components import note

if spaces is not None:
    @spaces.GPU
    def zerogpu_runtime_marker() -> str:
        """Satisfy ZeroGPU startup detection; the application does not use the GPU."""
        return "ok"
else:
    def zerogpu_runtime_marker() -> str:
        return "ok"

SCREEN_ORDER = [
    "Healthcare Overview",
    "Infrastructure Management",
    "Facility Locator and Mapping",
    "Facility Utilization Analytics",
    "Medical Workforce Management",
    "Preventive Health Programmes",
    "Screening Operations",
    "Diagnostic Laboratory Management",
    "Patient and Citizen Registry",
    "Referral Coordination",
    "Health Awareness Campaigns",
    "Notification Management",
    "Substance-Use Prevention",
    "Healthcare Employment",
    "Reports and Analytics",
    "Administration and Settings",
    "Citizen Portal",
]

ALL_SCREENS = SCREEN_ORDER

ROLE_SCREENS = {
    "District Administrator": ALL_SCREENS,
    "State Health Administrator": ALL_SCREENS,
    "District Medical Officer": [
        "Healthcare Overview", "Infrastructure Management", "Facility Locator and Mapping",
        "Facility Utilization Analytics", "Medical Workforce Management", "Preventive Health Programmes",
        "Screening Operations", "Diagnostic Laboratory Management", "Patient and Citizen Registry",
        "Referral Coordination", "Health Awareness Campaigns", "Notification Management",
        "Substance-Use Prevention", "Healthcare Employment", "Reports and Analytics", "Citizen Portal",
    ],
    "Facility Administrator": [
        "Healthcare Overview", "Infrastructure Management", "Facility Locator and Mapping",
        "Facility Utilization Analytics", "Medical Workforce Management", "Preventive Health Programmes",
        "Screening Operations", "Diagnostic Laboratory Management", "Patient and Citizen Registry",
        "Referral Coordination", "Health Awareness Campaigns", "Notification Management",
        "Substance-Use Prevention", "Healthcare Employment", "Reports and Analytics", "Citizen Portal",
    ],
    "Medical Officer": [
        "Healthcare Overview", "Facility Locator and Mapping", "Preventive Health Programmes",
        "Screening Operations", "Diagnostic Laboratory Management", "Patient and Citizen Registry",
        "Referral Coordination", "Substance-Use Prevention", "Health Awareness Campaigns",
        "Reports and Analytics", "Citizen Portal",
    ],
    "Laboratory Administrator": [
        "Healthcare Overview", "Diagnostic Laboratory Management", "Patient and Citizen Registry",
        "Referral Coordination", "Notification Management", "Reports and Analytics", "Citizen Portal",
    ],
    "Community Health Worker": [
        "Healthcare Overview", "Facility Locator and Mapping", "Preventive Health Programmes",
        "Screening Operations", "Patient and Citizen Registry", "Referral Coordination",
        "Health Awareness Campaigns", "Substance-Use Prevention", "Citizen Portal",
    ],
    "Citizen": ["Citizen Portal", "Facility Locator and Mapping"],
}

BUILDERS = {
    "Healthcare Overview": dashboard.build,
    "Infrastructure Management": infrastructure.build,
    "Facility Locator and Mapping": locator.build,
    "Facility Utilization Analytics": utilization.build,
    "Medical Workforce Management": workforce.build,
    "Preventive Health Programmes": prevention.build,
    "Screening Operations": screening_ops.build,
    "Diagnostic Laboratory Management": diagnostics.build,
    "Patient and Citizen Registry": registry.build,
    "Referral Coordination": referrals.build,
    "Health Awareness Campaigns": campaigns.build,
    "Notification Management": notifications.build,
    "Substance-Use Prevention": substance.build,
    "Healthcare Employment": employment.build,
    "Reports and Analytics": reports.build,
    "Administration and Settings": admin.build,
    "Citizen Portal": citizen.build,
}


def bootstrap() -> None:
    """Create the SQLite schema and seed deterministic demo data if empty."""
    init_db()
    with session_scope() as session:
        seed_database(session)


def toggle_screens(selected: str):
    return [gr.update(visible=(key == selected)) for key in SCREEN_ORDER]


def on_role_change(role: str, selected: str):
    available = ROLE_SCREENS.get(role, SCREEN_ORDER)
    target = selected if selected in available else available[0]
    return (
        theme.role_banner_html(role),
        gr.update(choices=available, value=target),
        *[gr.update(visible=(key == target)) for key in SCREEN_ORDER],
    )


def build_app() -> gr.Blocks:
    bootstrap()
    with gr.Blocks(
        title=APP_NAME,
        theme=theme.gradio_theme(),
        css=theme.CSS,
        analytics_enabled=False,
    ) as demo:
        gr.HTML(theme.header_html())
        with gr.Row():
            with gr.Column(scale=1, min_width=250):
                role = gr.Dropdown(
                    DEMO_ROLES, value="District Administrator", label="Demo role switcher"
                )
                role_banner = gr.HTML(theme.role_banner_html("District Administrator"))
                nav = gr.Radio(
                    SCREEN_ORDER, value="Healthcare Overview", label="Operations workspace",
                    elem_id="bhd-nav",
                )
                gr.HTML(note(
                    "Role switching is a demonstration control only. No authentication is performed and no "
                    "real access control is implemented. Do not enter real patient information."
                ))
            with gr.Column(scale=5):
                groups = {}
                for key in SCREEN_ORDER:
                    with gr.Column(visible=(key == "Healthcare Overview")) as column:
                        BUILDERS[key](demo)
                    groups[key] = column
        gr.HTML(note(
            "Enterprise healthcare operations and public-health intelligence workspace with a separate Citizen "
            "Portal. All records are fictional demo data. Not a medical device. A screening observation is not a "
            "diagnosis. Emergency symptoms require immediate emergency care. Laboratory screens are status-only "
            "and never show clinical values. See Administration and Settings for the privacy and safety statement."
        ))

        nav.change(toggle_screens, inputs=[nav], outputs=[groups[key] for key in SCREEN_ORDER])
        role.change(
            on_role_change,
            inputs=[role, nav],
            outputs=[role_banner, nav] + [groups[key] for key in SCREEN_ORDER],
        )
    return demo


def main() -> None:
    demo = build_app()
    server_name = os.getenv("BHDC_SERVER_NAME", "0.0.0.0")
    server_port = int(os.getenv("PORT", os.getenv("BHDC_SERVER_PORT", "7860")))
    demo.queue(default_concurrency_limit=8).launch(
        server_name=server_name,
        server_port=server_port,
        share=False,
        show_error=True,
    )


if __name__ == "__main__":
    main()
