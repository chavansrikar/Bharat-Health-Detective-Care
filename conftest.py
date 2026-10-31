"""Test bootstrap: use an isolated temporary SQLite database."""
from __future__ import annotations

import os
import tempfile
from pathlib import Path

import pytest

_TEST_DB = Path(tempfile.gettempdir()) / "bhd_test.db"
os.environ["BHDC_DB_PATH"] = str(_TEST_DB)
if _TEST_DB.exists():
    _TEST_DB.unlink()

from src.database import init_db, session_scope  # noqa: E402
from src.seed import reset_database, seed_database  # noqa: E402


@pytest.fixture(autouse=True)
def fresh_db():
    init_db()
    with session_scope() as session:
        reset_database(session)
    yield
