"""Patient and Citizen Registry — synthetic longitudinal demo records."""
from __future__ import annotations

import gradio as gr
import pandas as pd

from src.config import DISTRICTS
from src.database import session_scope
from src.models import AuditEvent, LabOrder, Participant, Referral, Screening
from src.services import citizen_service, screening_service
from src.ui.components import detail_card, kpi_cards, note, section

AGE_BANDS = ["0-5", "6-17", "18-29", "30-44", "45-59", "60+"]
GENDERS = ["Not recorded", "Female", "Male", "Other"]
KPI_DEFS = [
    ("participants", "Registered people", ""),
    ("consent", "Consent recorded", ""),
    ("screened", "With screening record", ""),
    ("referred", "With referral record", ""),
    ("pending_review", "Reviews pending", "warn"),
]

COLUMNS = ["code", "alias", "age_band", "gender", "locality", "district", "consent", "assigned_worker",
           "screenings", "referrals"]


def _rows(session, text, district, gender, age_band):
    stmt = session.query(Participant).order_by(Participant.synthetic_code)
    if text and text.strip():
        like = f"%{text.strip().lower()}%"
        stmt = stmt.filter(
            Participant.synthetic_code.ilike(like)
            | Participant.display_name_alias.ilike(like)
            | Participant.locality.ilike(like)
        )
    if district != "All":
        stmt = stmt.filter(Participant.district == district)
    if gender != "All":
        stmt = stmt.filter(Participant.gender == gender)
    if age_band != "All":
        stmt = stmt.filter(Participant.age_band == age_band)
    participants = stmt.all()
    rows = []
    for p in participants:
        rows.append({
            "code": p.synthetic_code, "alias": p.display_name_alias, "age_band": p.age_band,
            "gender": p.gender, "locality": p.locality, "district": p.district,
            "consent": p.consent_status, "assigned_worker": p.assigned_worker,
            "screenings": session.query(Screening).filter(Screening.participant_id == p.id).count(),
            "referrals": session.query(Referral).filter(Referral.participant_id == p.id).count(),
        })
    return participants, rows


def _detail(session, participant_id):
    participant = session.get(Participant, participant_id)
    if participant is None:
        return note("Select a registry record.")
    records = citizen_service.all_records(session, participant_id)
    record_lines = [
        f"<b>{r['reference']}</b> · {r['detail']} · {r['date']} · <b>{r['status']}</b>"
        for r in records
    ] or ["No linked demo records."]
    return detail_card(
        f"{participant.synthetic_code} — {participant.display_name_alias}",
        [
            f"Age band: <b>{participant.age_band}</b> · Gender: <b>{participant.gender}</b>",
            f"Locality: {participant.locality}, {participant.district}",
            f"Consent: <b>{participant.consent_status}</b> · Assigned worker: {participant.assigned_worker}",
            "<div style='margin-top:6px'><b>Linked records</b></div>",
            *record_lines,
        ],
        "Synthetic record. No Aadhaar, ABHA or phone numbers are stored. Screening observations are not diagnoses.",
    )


def refresh(text, district, gender, age_band):
    with session_scope() as session:
        participants, rows = _rows(session, text, district, gender, age_band)
        kpis = {
            "participants": len(participants),
            "consent": sum(1 for p in participants if p.consent_status.startswith("Granted")),
            "screened": sum(1 for row in rows if row["screenings"]),
            "referred": sum(1 for row in rows if row["referrals"]),
            "pending_review": session.query(Screening).filter(
                Screening.review_status == "Pending clinician review"
            ).count(),
        }
        choices = [(f"{p.synthetic_code} — {p.display_name_alias}", p.id) for p in participants]
        detail_value = _detail(session, participants[0].id) if participants else note("No matching registry records.")
    return (
        kpi_cards(kpis, KPI_DEFS),
        pd.DataFrame(rows, columns=COLUMNS),
        gr.update(choices=choices, value=choices[0][1] if choices else None),
        detail_value,
    )


def _register(alias, age_band, gender, locality, district, consent, worker):
    if not consent.startswith("Granted"):
        return "Consent is required to create a demo registry record.", gr.skip(), gr.skip()
    try:
        with session_scope() as session:
            participant = screening_service.register_participant(
                session, alias=alias, age_band=age_band, locality=locality,
                consent_status=consent, assigned_worker=worker,
            )
            participant.gender = gender
            participant.district = district
            session.add(AuditEvent(
                actor_role="Community Health Worker", action="Registered participant",
                entity_type="participant", entity_id=participant.synthetic_code, note=participant.display_name_alias,
            ))
            session.flush()
            participants, rows = _rows(session, "", "All", "All", "All")
            choices = [(f"{p.synthetic_code} — {p.display_name_alias}", p.id) for p in participants]
            detail_value = _detail(session, participant.id)
        return (
            f"Registry record {participant.synthetic_code} created.",
            pd.DataFrame(rows, columns=COLUMNS),
            gr.update(choices=choices, value=participant.id),
            detail_value,
        )
    except Exception as exc:  # noqa: BLE001
        return f"Could not register participant: {exc}", gr.skip(), gr.skip(), gr.skip()


def build(demo) -> None:
    gr.HTML(section("Patient and Citizen Registry"))
    gr.HTML(note(
        "Synthetic longitudinal records for demonstration only. This registry links screening, referral and "
        "diagnostic status views without storing real identifiers. Consent is recorded explicitly."
    ))
    with gr.Row():
        text = gr.Textbox(label="Search code, alias or locality", scale=2)
        district = gr.Dropdown(["All"] + DISTRICTS, value="All", label="District")
        gender = gr.Dropdown(["All"] + GENDERS, value="All", label="Gender")
        age_band = gr.Dropdown(["All"] + AGE_BANDS, value="All", label="Age band")
        btn = gr.Button("Search registry", variant="primary")
    kpis = gr.HTML()
    table = gr.Dataframe(interactive=False, wrap=True, label="Registry records")
    with gr.Row():
        with gr.Column(scale=3):
            choice = gr.Dropdown(label="Registry detail", choices=[])
            detail_html = gr.HTML()
        with gr.Column(scale=2):
            with gr.Accordion("Register a demo participant", open=False):
                r_alias = gr.Textbox(label="Display alias")
                r_age = gr.Dropdown(AGE_BANDS, value="30-44", label="Age band")
                r_gender = gr.Dropdown(GENDERS, value="Not recorded", label="Gender")
                r_locality = gr.Textbox(label="Locality")
                r_district = gr.Dropdown(DISTRICTS, value=DISTRICTS[0], label="District")
                r_consent = gr.Dropdown(
                    ["Granted (demo)", "Declined (demo)"], value="Granted (demo)", label="Consent"
                )
                r_worker = gr.Textbox(label="Assigned worker", value="Unassigned")
                r_btn = gr.Button("Register participant", variant="primary")
                r_msg = gr.Markdown()

    outputs = [kpis, table, choice, detail_html]
    btn.click(refresh, inputs=[text, district, gender, age_band], outputs=outputs)
    choice.change(lambda pid: _detail_for(pid), inputs=[choice], outputs=[detail_html])
    r_btn.click(
        _register, inputs=[r_alias, r_age, r_gender, r_locality, r_district, r_consent, r_worker],
        outputs=[r_msg, table, choice, detail_html],
    )
    demo.load(refresh, inputs=[text, district, gender, age_band], outputs=outputs)


def _detail_for(participant_id):
    if not participant_id:
        return note("Select a registry record.")
    with session_scope() as session:
        return _detail(session, int(participant_id))
