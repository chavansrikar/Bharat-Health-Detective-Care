from src.database import session_scope
from src.seed import reset_database
from src.services import reporting_service


def test_dashboard_kpis_match_database():
    with session_scope() as session:
        kpis = reporting_service.dashboard_kpis(session)
    assert kpis["facilities"] == 30
    assert kpis["active_facilities"] == 29
    assert kpis["workforce"] == 22
    assert kpis["screening_events"] == 7
    assert kpis["referrals_open"] >= 1
    assert 0 <= kpis["coverage_pct"] <= 100


def test_district_filter_reduces_scope():
    with session_scope() as session:
        full = reporting_service.overview_kpis(session)
        nalgonda = reporting_service.overview_kpis(session, district="Nalgonda")
        ids = reporting_service.scope_ids(session, district="Nalgonda")
    assert 0 < nalgonda["total_facilities"] < full["total_facilities"]
    assert len(ids) == nalgonda["total_facilities"]


def test_csv_export_has_rows():
    with session_scope() as session:
        csv_text = reporting_service.export_csv(session, "Facilities")
    assert csv_text
    lines = csv_text.strip().splitlines()
    assert lines[0].startswith("code,name,type")
    assert len(lines) > 10


def test_reset_restores_seed():
    with session_scope() as session:
        kpis_before = reporting_service.dashboard_kpis(session)
        reset_database(session)
        kpis_after = reporting_service.dashboard_kpis(session)
    assert kpis_before == kpis_after


def test_reports_summary_percentages():
    with session_scope() as session:
        summary = reporting_service.reports_summary(session)
    assert 0 <= summary["referral_completion_pct"] <= 100
    assert 0 <= summary["screening_review_pct"] <= 100
    assert summary["avg_utilization_pct"] >= 0
