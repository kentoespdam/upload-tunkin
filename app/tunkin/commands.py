"""UploadKpiCommand — CQRS command for the Tunkin upload pipeline.

Wraps the gate → parser → upsert flow into a single dependency-injectable
command so the write path can be called from non-HTTP entrypoints (CLI/worker).
"""

from typing import Annotated

from fastapi import Depends, UploadFile

from app.tunkin.repository import KPIRepository, get_kpi_repository
from app.tunkin.services import FileGate, KPISheetParser, get_file_gate, get_kpi_sheet_parser
from app.tunkin.schemas import UpsertResult


class UploadKpiCommand:
    """Composable command: gate → parse → upsert."""

    def __init__(
        self,
        file_gate: FileGate,
        parser: KPISheetParser,
        kpi_repo: KPIRepository,
    ):
        self._file_gate = file_gate
        self._parser = parser
        self._kpi_repo = kpi_repo

    async def execute(self, file: UploadFile) -> UpsertResult:
        """Validate, parse, and upsert a KPI upload file."""
        data = await self._file_gate.check(file)
        records = self._parser.parse(data)
        return self._kpi_repo.upsert_batch(records)


def get_upload_kpi_command(
    file_gate: Annotated[FileGate, Depends(get_file_gate)],
    parser: Annotated[KPISheetParser, Depends(get_kpi_sheet_parser)],
    kpi_repo: Annotated[KPIRepository, Depends(get_kpi_repository)],
) -> UploadKpiCommand:
    """Factory: compose three dependencies into one command."""
    return UploadKpiCommand(file_gate, parser, kpi_repo)