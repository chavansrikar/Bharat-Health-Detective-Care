import pytest

from src.database import session_scope
from src.services import lab_service


def test_advance_lab_workflow():
    with session_scope() as session:
        order = lab_service.order_choices(session)[0]
        advanced = lab_service.advance_order(session, order[1])
    assert advanced.sample_status in {"Sample collected", "Received by lab", "Processing", "Result available"}


def test_mark_reviewed_requires_result():
    with session_scope() as session:
        orders = lab_service.list_orders(session)
        ordered = next(o for o in orders if o["result_status"] != "Result available")
        with pytest.raises(ValueError):
            lab_service.mark_reviewed(session, ordered["order_id"])


def test_verified_report_can_be_delivered():
    with session_scope() as session:
        orders = lab_service.list_orders(session)
        verified = next(o for o in orders if o["report_status"] == "Verified")
        delivered = lab_service.deliver_report(session, verified["order_id"])
        assert delivered.report_status == "Delivered"
        pending = next(o for o in orders if o["report_status"] == "Pending result entry")
        with pytest.raises(ValueError):
            lab_service.deliver_report(session, pending["order_id"])


def test_enter_result_creates_pending_review_status():
    with session_scope() as session:
        order = lab_service.order_choices(session)[1]
        updated = lab_service.enter_result(session, order[1])
        assert updated.report_status == "Result entered"
        assert updated.reviewer_status == "Awaiting clinician review"
        assert updated.result_status == "Result available"
