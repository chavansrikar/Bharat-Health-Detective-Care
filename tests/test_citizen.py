from datetime import datetime, timedelta

import pytest

from src.database import session_scope
from src.services import citizen_service, facility_service


def test_registration_requires_consent():
    with session_scope() as session:
        with pytest.raises(ValueError):
            citizen_service.register_citizen(session, "Citizen Test", "30-44", "Bhuvanagiri",
                                             consent_status="Declined (demo)")
        participant = citizen_service.register_citizen(
            session, "Citizen Test", "30-44", "Bhuvanagiri", "Female", "Yadadri Bhuvanagiri"
        )
        profile = citizen_service.citizen_profile(session, participant.id)
    assert profile["district"] == "Yadadri Bhuvanagiri"
    assert profile["consent"].startswith("Granted")


def test_appointment_lifecycle_and_reminders():
    with session_scope() as session:
        participant = citizen_service.get_participant(session, 1)
        facility = facility_service.search_facilities(session, active="Active")[0]
        appointment = citizen_service.create_appointment(
            session, participant.id, facility.id, "NCD screening",
            datetime.now() + timedelta(days=5), "Demo callback", "Demo note",
        )
        assert appointment.status == "Requested"
        cancelled = citizen_service.cancel_appointment(session, appointment.id)
        assert cancelled.status == "Cancelled"
        reminders = citizen_service.reminders(session, participant.id)
        assert reminders


def test_appointment_rejects_past_and_inactive_facility():
    with session_scope() as session:
        inactive = facility_service.search_facilities(session, active="Inactive")
        assert inactive
        with pytest.raises(ValueError):
            citizen_service.create_appointment(
                session, 1, inactive[0].id, "NCD screening", datetime.now() + timedelta(days=2)
            )
        active = facility_service.search_facilities(session, active="Active")[0]
        with pytest.raises(ValueError):
            citizen_service.create_appointment(
                session, 1, active.id, "NCD screening", datetime.now() - timedelta(days=1)
            )
