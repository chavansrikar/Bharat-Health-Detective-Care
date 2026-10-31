"""Diagnostic Laboratory Management — status-only sample and report workflow."""
from __future__ import annotations

import gradio as gr
import pandas as pd

from src.config import LAB_PRIORITIES, REPORT_STATUSES
from src.database import session_scope
from src.models import AuditEvent
from src.services import lab_service, reporting_service
from src.ui.components import detail_card, kpi_cards, note, scope_controls, section

KPI_DEFS = [
    ("orders", "Lab orders", ""),
    ("pending_reports", "Reports pending", "warn"),
    ("lab_awaiting_review", "Awaiting clinician review", "warn"),
    ("delivered", "Delivered", ""),
    ("verified", "Verified", ""),
]

COLUMNS = ["order_code", "referral", "lab", "test_category", "priority", "requested_by",
           "sample_status", "report_status", "reviewer_status", "updated_at"]


def _detail(session, order_id):
    rows = [o for o in lab_service.list_orders(session) if o["order_id"] == order_id]
    if not rows:
        return note("Select a laboratory order.")
    o = rows[0]
    return detail_card(
        f"{o['order_code']} — {o['test_category']}",
        [
            f"Referral: <b>{o['referral']}</b> · Laboratory: <b>{o['lab']}</b>",
            f"Priority: <b>{o['priority']}</b> · Requested by: {o['requested_by']}",
            f"Sample stage: <b>{o['sample_status']}</b>",
            f"Report stage: <b>{o['report_status']}</b> · Review: <b>{o['reviewer_status']}</b>",
            f"Last updated: {o['updated_at']}",
            f"Demo note: {o['demo_note'] or 'No clinical value is stored in this prototype.'}",
        ],
        "Status-only demo workflow. No clinical values are fabricated, displayed or transmitted. "
        "Results require clinician verification before any release.",
    )


def refresh(state, district, mandal, category, active, report_status, priority):
    args = dict(state=state, district=district, mandal=mandal, category=category, active=active)
    with session_scope() as session:
        ids = reporting_service.scope_ids(session, **args)
        orders = lab_service.list_orders(session, facility_ids=ids)
        if report_status != "All":
            orders = [o for o in orders if o["report_status"] == report_status]
        if priority != "All":
            orders = [o for o in orders if o["priority"] == priority]
        all_orders = lab_service.list_orders(session, facility_ids=ids)
        kpis = reporting_service.overview_kpis(session, **args)
        kpis["orders"] = len(all_orders)
        kpis["delivered"] = sum(1 for o in all_orders if o["report_status"] == "Delivered")
        kpis["verified"] = sum(1 for o in all_orders if o["report_status"] == "Verified")
        choices = [(f"{o['order_code']} — {o['test_category']}", o["order_id"]) for o in orders]
        detail_value = _detail(session, orders[0]["order_id"]) if orders else note("No orders match the filters.")
    return (
        kpi_cards(kpis, KPI_DEFS),
        pd.DataFrame(orders, columns=COLUMNS),
        gr.update(choices=choices, value=choices[0][1] if choices else None),
        detail_value,
        note(reporting_service.scope_label(state, district, mandal, category, active)),
    )


def _action(order_id, action):
    if not order_id:
        return "Select a laboratory order.", gr.skip()
    try:
        with session_scope() as session:
            if action == "Advance sample stage":
                order = lab_service.advance_order(session, int(order_id))
                message = f"Sample stage advanced to '{order.sample_status}'."
            elif action == "Enter result status":
                order = lab_service.enter_result(session, int(order_id))
                message = "Result status entered. The report now awaits clinician review; no clinical value is stored."
            elif action == "Verify report":
                order = lab_service.verify_report(session, int(order_id))
                message = "Report verified. Delivery can now be recorded."
            elif action == "Mark delivered":
                order = lab_service.deliver_report(session, int(order_id))
                message = "Report marked as delivered in the demo workflow."
            else:
                return "Unknown action.", gr.skip()
            session.add(AuditEvent(
                actor_role="Laboratory Administrator", action=action,
                entity_type="lab_order", entity_id=order.order_code, note=order.report_status,
            ))
            detail_value = _detail(session, order.id)
            choices = lab_service.order_choices(session)
        return message, detail_value, gr.update(choices=choices, value=order.id)
    except Exception as exc:  # noqa: BLE001
        return f"Could not update laboratory order: {exc}", gr.skip(), gr.skip()


def build(demo) -> None:
    gr.HTML(section("Diagnostic Laboratory Management"))
    gr.HTML(note(
        "Sample and report stages are tracked as status-only demo records. This module never generates, guesses "
        "or displays clinical result values. A report is released only after clinician verification."
    ))
    controls = scope_controls()
    with gr.Row():
        report_status = gr.Dropdown(["All"] + REPORT_STATUSES, value="All", label="Report status")
        priority = gr.Dropdown(["All"] + LAB_PRIORITIES, value="All", label="Priority")
        btn = gr.Button("Refresh laboratory worklist", variant="primary")
    kpis = gr.HTML()
    scope_note = gr.HTML()
    table = gr.Dataframe(interactive=False, wrap=True, label="Laboratory orders")
    with gr.Row():
        with gr.Column(scale=3):
            detail_choice = gr.Dropdown(label="Order detail", choices=[])
            detail_html = gr.HTML()
        with gr.Column(scale=2):
            gr.HTML(section("Workflow action"))
            gr.HTML(note(
                "Order → sample collected → received → processing → result status → clinician review. "
                "Delivery requires a verified report."
            ))
            action = gr.Dropdown(
                ["Advance sample stage", "Enter result status", "Verify report", "Mark delivered"],
                value="Advance sample stage", label="Action",
            )
            action_btn = gr.Button("Apply workflow action", variant="primary")
            action_msg = gr.Markdown()

    outputs = [kpis, table, detail_choice, detail_html, scope_note]
    btn.click(refresh, inputs=list(controls) + [report_status, priority], outputs=outputs)
    detail_choice.change(
        lambda oid: _detail_for(oid), inputs=[detail_choice], outputs=[detail_html]
    )
    action_btn.click(
        _action, inputs=[detail_choice, action],
        outputs=[action_msg, detail_html, detail_choice],
    )
    demo.load(refresh, inputs=list(controls) + [report_status, priority], outputs=outputs)


def _detail_for(order_id):
    if not order_id:
        return note("Select a laboratory order.")
    with session_scope() as session:
        return _detail(session, int(order_id))
