import pytest

from datetime import date

from src.database import session_scope
from src.models import Facility
from src.services import screening_service


def test_record_and_review_screening():
    with session_scope() as session:
        participant = screening_service.register_participant(
            session, "Alias Test", "31-45", "Bhuvanagiri"
        )
        programmes = screening_service.list_programmes(session)
        facility = session.query(Facility).first()
        event = screening_service.create_event(
            session, programmes[0].id, facility.id, "Test event", date.today()
        )
        before = screening_service.pending_review_count(session)
        screening = screening_service.record_screening(
            session, participant.id, event.id, "Blood pressure",
            "Demo observation", "Needs clinician review",
        )
        assert screening.review_status == "Pending clinician review"
        assert screening_service.pending_review_count(session) == before + 1
        reviewed = screening_service.review_screening(session, screening.id, "Dr Test", "Reviewed")
        assert reviewed.review_status == "Reviewed"
        assert reviewed.reviewed_by == "Dr Test"


def test_double_review_rejected():
    with session_scope() as session:
        queue = screening_service.review_queue(session)
        assert queue
        screening_id = queue[0]["screening_id"]
        screening_service.review_screening(session, screening_id, "Dr Test")
        with pytest.raises(ValueError):
            screening_service.review_screening(session, screening_id, "Dr Test")
