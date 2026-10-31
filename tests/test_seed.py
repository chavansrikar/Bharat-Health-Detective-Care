from src.database import session_scope
from src.seed import seed_database


def test_seed_counts_are_deterministic():
    with session_scope() as session:
        counts = seed_database(session)
    assert counts["facilities"] == 30
    assert counts["participants"] == 40
    assert counts["programmes"] == 4
    assert counts["referrals"] == 16
    assert counts["lab_orders"] == 12
    assert counts["campaigns"] == 6
    assert counts["staff"] == 22
    assert counts["vacancies"] == 18
    assert counts["applications"] == 10
    assert counts["notifications"] == 6
    assert counts["substance_cases"] == 8
    assert counts["appointments"] == 8
    assert counts["services"] > 80
    assert counts["screenings"] == 30


def test_seed_is_idempotent():
    with session_scope() as session:
        first = seed_database(session)
    with session_scope() as session:
        second = seed_database(session)
    assert first == second
