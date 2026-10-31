import pytest

from src.database import session_scope
from src.models import Facility, Participant
from src.services import referral_service, screening_service


def _ids(session):
    participant = session.query(Participant).first()
    source = session.query(Facility).filter(Facility.code == "CHC-BH-01").one()
    phc = session.query(Facility).filter(Facility.code == "PHC-BH-01").one()
    hospital = session.query(Facility).filter(Facility.code == "DH-01").one()
    return participant, source, phc, hospital


def test_full_referral_lifecycle():
    with session_scope() as session:
        participant, source, phc, hospital = _ids(session)
        referral = referral_service.create_referral(
            session, participant.id, source.id, hospital.id, "Demo reason", "Routine"
        )
        for status in ["Sent", "Accepted", "Scheduled", "Attended", "Completed"]:
            referral = referral_service.transition_referral(session, referral.id, status)
        assert referral.status == "Completed"
        assert referral.closed_at is not None


def test_invalid_transition_rejected():
    with session_scope() as session:
        participant, source, phc, hospital = _ids(session)
        referral = referral_service.create_referral(
            session, participant.id, source.id, hospital.id, "Demo reason", "Routine"
        )
        with pytest.raises(ValueError):
            referral_service.transition_referral(session, referral.id, "Completed")


def test_urgent_referral_requires_emergency_capable_destination():
    with session_scope() as session:
        participant, source, phc, hospital = _ids(session)
        with pytest.raises(ValueError):
            referral_service.create_referral(
                session, participant.id, source.id, phc.id, "Urgent demo", "Urgent"
            )


def test_overdue_detection():
    with session_scope() as session:
        rows = referral_service.list_referrals(session, overdue_only=True)
    assert rows
    assert all(row["overdue"] for row in rows)
