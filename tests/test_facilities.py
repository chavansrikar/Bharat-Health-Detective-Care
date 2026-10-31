import pytest

from src.database import session_scope
from src.services import facility_service


def test_search_by_service_returns_matches():
    with session_scope() as session:
        results = facility_service.search_facilities(session, service="NCD screening")
    assert results
    assert all(any(s.service_name == "NCD screening" for s in f.services) for f in results)


def test_search_by_mandal_and_type():
    with session_scope() as session:
        results = facility_service.search_facilities(session, mandal="Choutuppal", facility_type="CHC")
    assert results
    assert all(f.mandal == "Choutuppal" and f.type == "CHC" for f in results)


def test_create_facility_persists():
    with session_scope() as session:
        created = facility_service.create_facility(
            session,
            {
                "name": "Test PHC", "type": "PHC", "mandal": "Alair",
                "locality": "Test village", "services": ["General medicine"],
            },
        )
        created_id = created.id
    with session_scope() as session:
        found = facility_service.get_facility(session, created_id)
        assert found is not None
        assert found.name == "Test PHC"
        assert found.verification_status == "Pending verification"
        assert found.services[0].service_name == "General medicine"


def test_create_facility_requires_fields():
    with session_scope() as session:
        with pytest.raises(ValueError):
            facility_service.create_facility(session, {"name": "", "type": "PHC"})


def test_utilization_rows_have_formula_fields():
    with session_scope() as session:
        rows = facility_service.utilization_rows(session)
    assert len(rows) == 30
    for row in rows:
        assert 0 <= row["utilization_pct"] <= 1000
        assert row["indicator"]
    assert any(row["completed_sessions"] > 0 for row in rows)


def test_filters_by_state_district_category_and_active():
    with session_scope() as session:
        nalgonda = facility_service.search_facilities(session, district="Nalgonda")
        diagnostics = facility_service.search_facilities(session, category="Diagnostics")
        inactive = facility_service.search_facilities(session, active="Inactive")
    assert nalgonda and all(f.district == "Nalgonda" for f in nalgonda)
    assert diagnostics and all(facility_service.category_of(f) == "Diagnostics" for f in diagnostics)
    assert len(inactive) == 1
    assert inactive[0].is_active is False
