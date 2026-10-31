import pytest

from src.database import session_scope
from src.models import Facility
from src.services import workforce_service


def test_workforce_summary_and_roles():
    with session_scope() as session:
        summary = workforce_service.workforce_summary(session)
        staff = workforce_service.list_staff(session, role="Medical Officer")
    assert summary["staff_total"] == 22
    assert summary["vacancy_gap"] > 0
    assert staff and all(row["role"] == "Medical Officer" for row in staff)


def test_create_and_fill_vacancy():
    with session_scope() as session:
        facility = session.query(Facility).first()
        vacancy = workforce_service.create_vacancy(
            session, facility.id, "Staff Nurse", 3, "High", "Demo cover"
        )
        assert vacancy.gap == 3
        updated = workforce_service.update_vacancy(session, vacancy.id, filled_count=3)
        assert updated.gap == 0
        assert updated.status == "Filled"


def test_application_workflow():
    with session_scope() as session:
        application = workforce_service.create_application(
            session, "Applicant Test (alias)", "Medical Officer", qualification="MBBS (demo)",
            experience_years=3,
        )
        assert application.status == "Received"
        updated = workforce_service.update_application_status(session, application.id, "Shortlisted")
        assert updated.status == "Shortlisted"
        with pytest.raises(ValueError):
            workforce_service.update_application_status(session, application.id, "Unknown")
