import pytest

from src.database import session_scope
from src.services import notification_service, substance_service


def test_substance_case_requires_consent_and_stays_confidential():
    with session_scope() as session:
        with pytest.raises(ValueError):
            substance_service.create_case(
                session, 1, "Tobacco", "Demo note", consent_status="Declined (demo)"
            )
        case = substance_service.create_case(
            session, 1, "Tobacco", "Voluntary demo support note", consent_status="Granted (demo)"
        )
        assert case.confidentiality_level.startswith("Restricted")
        assert case.counselling_status == "Screening recorded"
        updated = substance_service.update_case(
            session, case.id, status="Counselling scheduled", counsellor="Counsellor (alias)"
        )
        assert updated.counselling_status == "Counselling scheduled"
        assert updated.assigned_counsellor == "Counsellor (alias)"


def test_substance_status_validation():
    with session_scope() as session:
        case = substance_service.create_case(session, 1, "Alcohol")
        with pytest.raises(ValueError):
            substance_service.update_case(session, case.id, status="Not a status")


def test_notification_and_campaign_are_simulated_only():
    with session_scope() as session:
        notification = notification_service.create_notification(
            session, "Demo notice", "Demo message", "Facility administrators", "Planned SMS"
        )
        assert notification.status == "Draft"
        approved = notification_service.update_notification_status(
            session, notification.id, "Simulated — sent"
        )
        assert approved.status == "Simulated — sent"
        summary = notification_service.communication_summary(session)
        assert summary["delivered_for_real"] == 0

        campaign = notification_service.create_campaign(
            session, "Demo campaign", "Demo message", "Telugu", "Adults", "Bhuvanagiri", "Planned SMS"
        )
        assert campaign.delivery_status == "Simulated — not sent"
        scheduled = notification_service.update_campaign_status(
            session, campaign.id, "Scheduled (simulated)"
        )
        assert "simulated" in scheduled.delivery_status.lower()
