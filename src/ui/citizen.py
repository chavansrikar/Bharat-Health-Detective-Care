"""Citizen Portal — a separate, consent-led public experience."""
from __future__ import annotations

from datetime import datetime
from html import escape

import gradio as gr
import pandas as pd
import plotly.express as px

from src.config import APPOINTMENT_STATUSES, DISTRICTS
from src.database import session_scope
from src.services import citizen_service, facility_service
from src.ui.components import detail_card, emergency_html, note, section

AGE_BANDS = ["0-5", "6-17", "18-29", "30-44", "45-59", "60+"]
GENDERS = ["Not recorded", "Female", "Male", "Other"]
CONTACT_OPTIONS = ["Demo callback", "Demo SMS (simulated)", "No contact — walk-in guidance"]

RECORD_COLUMNS = ["record_type", "reference", "detail", "date", "status", "safety_note"]
APPOINTMENT_COLUMNS = ["appointment_code", "facility", "service", "preferred_date", "status", "contact_preference"]


def _parse_when(value: str):
    for fmt in ("%Y-%m-%d %H:%M", "%Y-%m-%d"):
        try:
            return datetime.strptime(value.strip(), fmt)
        except (AttributeError, ValueError):
            continue
    raise ValueError("Enter appointment date/time as YYYY-MM-DD HH:MM")


def _profile_html(session, participant_id):
    if not participant_id:
        return note("Choose or create a demo citizen profile to continue.")
    profile = citizen_service.citizen_profile(session, int(participant_id))
    return detail_card(
        f"{profile['code']} — {profile['alias']}",
        [
            f"Age band: {profile['age_band']} · Gender: {profile['gender']}",
            f"Locality: {escape(profile['locality'])}, {escape(profile['district'])}",
            f"Consent: <b>{escape(profile['consent'])}</b> · Assigned worker: {escape(profile['assigned_worker'])}",
        ],
        "This is a fictional demo profile. No real identity, phone number, Aadhaar or ABHA ID is stored.",
    )


def _reminders_html(items: list[str]) -> str:
    if not items:
        return note("No reminders.")
    points = "".join(f"<li>{escape(item)}</li>" for item in items)
    return f'<div class="bhd-detail"><div class="t">Your reminders</div><ul>{points}</ul></div>'


def _records_frame(session, participant_id):
    if not participant_id:
        return pd.DataFrame(columns=RECORD_COLUMNS)
    return pd.DataFrame(citizen_service.all_records(session, int(participant_id)), columns=RECORD_COLUMNS)


def _appointments_frame(session, participant_id):
    if not participant_id:
        return pd.DataFrame(columns=APPOINTMENT_COLUMNS)
    return pd.DataFrame(citizen_service.list_appointments(session, int(participant_id)), columns=APPOINTMENT_COLUMNS)


def _appointment_choices(session, participant_id):
    return citizen_service.appointment_choices(session, int(participant_id)) if participant_id else []


def bundle(participant_id):
    with session_scope() as session:
        profile = _profile_html(session, participant_id)
        reminders = _reminders_html(citizen_service.reminders(session, int(participant_id))) if participant_id else _reminders_html([])
        appointments = _appointments_frame(session, participant_id)
        records = _records_frame(session, participant_id)
        choices = _appointment_choices(session, participant_id)
    return profile, reminders, appointments, records, gr.update(choices=choices, value=choices[0][1] if choices else None)


def _register(alias, age_band, gender, locality, district, consent):
    try:
        with session_scope() as session:
            participant = citizen_service.register_citizen(
                session, alias, age_band, locality, gender, district, consent
            )
            choices = citizen_service.participant_choices(session)
        profile, reminders, appointments, records, appointment_update = bundle(participant.id)
        return (
            f"Demo citizen profile {participant.synthetic_code} created with consent recorded.",
            gr.update(choices=choices, value=participant.id),
            profile, reminders, appointments, records, appointment_update,
        )
    except Exception as exc:  # noqa: BLE001
        return f"Could not create profile: {exc}", gr.skip(), gr.skip(), gr.skip(), gr.skip(), gr.skip(), gr.skip()


def _find(district, service):
    with session_scope() as session:
        options = citizen_service.facility_options(session, district=district, service=service)
        services = facility_service.facility_service_names(session)
    frame = pd.DataFrame(options, columns=["facility_id", "name", "type", "district", "mandal", "locality", "operating", "services"])
    if not options:
        fig = px.scatter(title="No active facilities match this search")
        fig.update_layout(height=360)
    else:
        coords = []
        with session_scope() as session:
            for row in options:
                facility = facility_service.get_facility(session, row["facility_id"])
                coords.append({
                    "facility": facility.name, "type": facility.type,
                    "lat": facility.latitude, "lon": facility.longitude, "mandal": facility.mandal,
                })
        fig = px.scatter(pd.DataFrame(coords), x="lon", y="lat", color="type", hover_name="facility",
                         hover_data=["mandal"], title="Schematic map — confirm by phone before travelling")
        fig.update_layout(height=380, margin=dict(l=10, r=10, t=44, b=10),
                          xaxis_title="Longitude (illustrative)", yaxis_title="Latitude (illustrative)")
    return frame, fig, gr.update(choices=["All"] + services, value=service)


def _book(participant_id, facility_id, service, when, contact, notes):
    if not participant_id:
        return "Choose or create a citizen profile first.", gr.skip(), gr.skip(), gr.skip()
    try:
        preferred = _parse_when(when)
        if not facility_id:
            raise ValueError("Choose a facility")
        if not service or not service.strip():
            raise ValueError("Enter the service you need")
        with session_scope() as session:
            appointment = citizen_service.create_appointment(
                session, int(participant_id), int(facility_id), service, preferred, contact, notes or ""
            )
            appointments = _appointments_frame(session, participant_id)
            choices = _appointment_choices(session, participant_id)
            reminders = _reminders_html(citizen_service.reminders(session, int(participant_id)))
        return (
            f"Appointment request {appointment.appointment_code} recorded as 'Requested'. This is not a confirmed "
            "booking — contact the facility to confirm.",
            appointments, reminders, gr.update(choices=choices, value=appointment.id),
        )
    except Exception as exc:  # noqa: BLE001
        return f"Could not request appointment: {exc}", gr.skip(), gr.skip(), gr.skip()


def _cancel(participant_id, appointment_id):
    if not participant_id or not appointment_id:
        return "Choose a profile and an appointment.", gr.skip(), gr.skip(), gr.skip()
    try:
        with session_scope() as session:
            citizen_service.cancel_appointment(session, int(appointment_id))
            appointments = _appointments_frame(session, participant_id)
            choices = _appointment_choices(session, participant_id)
            reminders = _reminders_html(citizen_service.reminders(session, int(participant_id)))
        return "Appointment request cancelled in the demo portal.", appointments, reminders, gr.update(
            choices=choices, value=choices[0][1] if choices else None
        )
    except Exception as exc:  # noqa: BLE001
        return f"Could not cancel appointment: {exc}", gr.skip(), gr.skip(), gr.skip()


def _services_for_facility(facility_id):
    if not facility_id:
        return gr.update(choices=[])
    with session_scope() as session:
        options = citizen_service.service_options_for_facility(session, int(facility_id))
    return gr.update(choices=options, value=options[0] if options else None)


def _awareness():
    with session_scope() as session:
        campaigns = pd.DataFrame(citizen_service.awareness_feed(session))
        notifications = pd.DataFrame(citizen_service.citizen_notifications(session))
    return campaigns, notifications


def _initial():
    with session_scope() as session:
        choices = citizen_service.participant_choices(session)
        facilities = citizen_service.facility_options(session, district="All", service="All")
        facility_choices = [(f"{f['name']} — {f['mandal']}", f["facility_id"]) for f in facilities]
        services = facility_service.facility_service_names(session)
    first = choices[0][1] if choices else None
    profile, reminders, appointments, records, appointment_update = bundle(first)
    find_frame, find_fig, service_update = _find("All", "All")
    campaigns, notifications = _awareness()
    return (
        gr.update(choices=choices, value=first),
        profile, reminders, appointments, records, appointment_update,
        gr.update(choices=facility_choices, value=facility_choices[0][1] if facility_choices else None),
        service_update, find_frame, find_fig, campaigns, notifications,
    )


def build(demo) -> None:
    gr.HTML(section("Citizen Portal"))
    gr.HTML(emergency_html())
    gr.HTML(note(
        "A separate public experience for reminder guidance, finding listed facilities and requesting appointments. "
        "It is not a medical service and does not confirm bookings or availability. All profiles are fictional demos."
    ))
    with gr.Row():
        profile_choice = gr.Dropdown(label="Continue as demo citizen profile", choices=[], scale=4)
        load_btn = gr.Button("Open profile", variant="primary")
    with gr.Accordion("Create a demo citizen profile (consent required)", open=False):
        with gr.Row():
            alias = gr.Textbox(label="Display alias", placeholder="Citizen alias")
            age_band = gr.Dropdown(AGE_BANDS, value="30-44", label="Age band")
            gender = gr.Dropdown(GENDERS, value="Not recorded", label="Gender")
        with gr.Row():
            locality = gr.Textbox(label="Locality")
            district = gr.Dropdown(DISTRICTS, value=DISTRICTS[0], label="District")
            consent = gr.Dropdown(["Granted (demo)", "Declined (demo)"], value="Granted (demo)", label="Consent")
        register_btn = gr.Button("Create profile")
        register_msg = gr.Markdown()

    with gr.Row():
        with gr.Column(scale=3):
            profile_html = gr.HTML()
        with gr.Column(scale=2):
            reminders_html = gr.HTML()

    with gr.Tabs():
        with gr.Tab("Appointments"):
            gr.HTML(note(
                "Appointment requests are demo records only. Contact the facility directly to confirm. "
                "For emergencies, use emergency services now."
            ))
            appointment_table = gr.Dataframe(interactive=False, wrap=True, label="My appointment requests")
            with gr.Row():
                with gr.Column():
                    facility = gr.Dropdown(label="Facility", choices=[])
                    service = gr.Dropdown(label="Service", choices=[])
                    when = gr.Textbox(label="Preferred date/time (YYYY-MM-DD HH:MM)")
                    contact = gr.Dropdown(CONTACT_OPTIONS, value=CONTACT_OPTIONS[0], label="Contact preference")
                    notes = gr.Textbox(label="Notes for the facility", lines=2)
                    book_btn = gr.Button("Request appointment", variant="primary")
                    book_msg = gr.Markdown()
                with gr.Column():
                    cancel_choice = gr.Dropdown(label="Cancel an appointment request", choices=[])
                    cancel_btn = gr.Button("Cancel request")
                    cancel_msg = gr.Markdown()

        with gr.Tab("My health records"):
            gr.HTML(note(
                "Records are status-only. Screening observations are not diagnoses; laboratory results are never "
                "displayed as values in this prototype. Ask a clinician to explain any record."
            ))
            records_table = gr.Dataframe(interactive=False, wrap=True, label="Screening, referral and diagnostic status")

        with gr.Tab("Find care"):
            gr.HTML(note("Search active listed facilities. Call ahead to confirm services and timings."))
            with gr.Row():
                find_district = gr.Dropdown(["All"] + DISTRICTS, value="All", label="District")
                find_service = gr.Dropdown(["All"], value="All", label="Service")
                find_btn = gr.Button("Find facilities", variant="primary")
            find_table = gr.Dataframe(interactive=False, wrap=True, label="Listed facilities")
            find_plot = gr.Plot(label="Schematic map")

        with gr.Tab("Awareness and notices"):
            awareness_table = gr.Dataframe(interactive=False, wrap=True, label="Approved awareness messages")
            notices_table = gr.Dataframe(interactive=False, wrap=True, label="Citizen notices")

    outputs = [
        profile_html, reminders_html, appointment_table, records_table, cancel_choice,
        facility, service, find_table, find_plot, awareness_table, notices_table,
    ]
    load_btn.click(bundle, inputs=[profile_choice], outputs=outputs[:5])
    register_btn.click(
        _register, inputs=[alias, age_band, gender, locality, district, consent],
        outputs=[register_msg, profile_choice, profile_html, reminders_html, appointment_table,
                 records_table, cancel_choice],
    )
    facility.change(_services_for_facility, inputs=[facility], outputs=[service])
    book_btn.click(
        _book, inputs=[profile_choice, facility, service, when, contact, notes],
        outputs=[book_msg, appointment_table, reminders_html, cancel_choice],
    )
    cancel_btn.click(
        _cancel, inputs=[profile_choice, cancel_choice],
        outputs=[cancel_msg, appointment_table, reminders_html, cancel_choice],
    )
    find_btn.click(_find, inputs=[find_district, find_service], outputs=[find_table, find_plot, find_service])
    demo.load(_initial, outputs=[profile_choice] + outputs)
