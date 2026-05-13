"""Unit tests for KPIRepository.upsert_batch — no FastAPI.

Uses a mock DatabaseHelper to verify query structure and params.

Run: uv run python test_kpi_repository.py
"""
from unittest.mock import MagicMock

from app.repositories.kpi_repository import KPIRepository
from app.models.kpi import KPIRecord, UpsertResult


class MockDBHelper:
    def __init__(self):
        self.called_with = None

    def save_update(self, query, params):
        self.called_with = (query, params)
        return 3  # 3 rows affected


def test_upsert_batch_correct_query():
    db = MockDBHelper()
    config = MagicMock()
    config.kpi_table_name = "tunkin_kpi"
    repo = KPIRepository(config, db)

    records = [
        KPIRecord(periode="002501", nipam="12345678", nominal=500000),
        KPIRecord(periode="002501", nipam="87654321", nominal=750000),
    ]
    result = repo.upsert_batch(records)

    assert isinstance(result, UpsertResult)
    assert result.status == "success"
    assert result.affected_rows == 3

    query, params = db.called_with
    assert "INSERT INTO tunkin_kpi" in query
    assert "ON DUPLICATE KEY UPDATE" in query
    assert params == [("002501", "12345678", 500000), ("002501", "87654321", 750000)]


def test_upsert_batch_empty_list():
    db = MockDBHelper()
    config = MagicMock()
    repo = KPIRepository(config, db)

    result = repo.upsert_batch([])
    assert result.affected_rows == 0
    assert db.called_with is None  # save_update NOT called


def test_upsert_batch_uses_table_name():
    db = MockDBHelper()
    config = MagicMock()
    config.kpi_table_name = "some_other_table"
    repo = KPIRepository(config, db)

    repo.upsert_batch([KPIRecord(periode="000001", nipam="00000001", nominal=100)])
    query, _ = db.called_with
    assert "some_other_table" in query


if __name__ == "__main__":
    tests = [test_upsert_batch_correct_query, test_upsert_batch_empty_list,
             test_upsert_batch_uses_table_name]
    for t in tests:
        t()
        print(f"PASS: {t.__name__}")
    print("\nAll KPIRepository unit tests passed!")
