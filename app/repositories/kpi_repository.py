"""KPIRepository — bulk upsert of KPI records to the database.

No FastAPI imports. Takes DatabaseHelper via constructor (Depends).
"""
from app.core.config import Config
from app.core.databases import DatabaseHelper
from app.models.kpi import KPIRecord, UpsertResult


class KPIRepository:
    """Repository for KPI table operations."""

    def __init__(self, config: Config, db_helper: DatabaseHelper):
        self._config = config
        self._db_helper = db_helper

    def upsert_batch(self, records: list[KPIRecord]) -> UpsertResult:
        """Bulk upsert KPI records using INSERT … ON DUPLICATE KEY UPDATE."""
        if not records:
            return UpsertResult(affected_rows=0)

        query = f"""
            INSERT INTO {self._config.kpi_table_name} (periode, nipam, nominal)
            VALUES (%s, %s, %s)
            ON DUPLICATE KEY UPDATE nominal = VALUES(nominal)
        """
        params = [(r.periode, r.nipam, r.nominal) for r in records]
        affected = self._db_helper.save_update(query, params)
        return UpsertResult(affected_rows=affected or 0)


def get_kpi_repository() -> KPIRepository:
    return KPIRepository(Config(), DatabaseHelper())
