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
    """Composable command: gate → parse → validate periode → upsert."""

    def __init__(
        self,
        file_gate: FileGate,
        parser: KPISheetParser,
        kpi_repo: KPIRepository,
    ):
        self._file_gate = file_gate
        self._parser = parser
        self._kpi_repo = kpi_repo

    async def execute(self, periode: str, file: UploadFile) -> UpsertResult:
        """Validate, parse, validate periode against file, and upsert KPI upload file."""
        data = await self._file_gate.check(file)
        records = self._parser.parse(data)

        # Validate all records match request periode
        normalized_periode = periode.zfill(6)
        mismatches = [
            f"Row {i+1}: expected {normalized_periode}, got {r.periode}"
            for i, r in enumerate(records)
            if r.periode != normalized_periode
        ]
        if mismatches:
            from fastapi import HTTPException
            raise HTTPException(
                status_code=400,
                detail=f"Periode tidak sesuai antara request dan data di file: {', '.join(mismatches[:5])}{'...' if len(mismatches) > 5 else ''}",
            )

        return self._kpi_repo.upsert_batch(records)


def get_upload_kpi_command(
    file_gate: Annotated[FileGate, Depends(get_file_gate)],
    parser: Annotated[KPISheetParser, Depends(get_kpi_sheet_parser)],
    kpi_repo: Annotated[KPIRepository, Depends(get_kpi_repository)],
) -> UploadKpiCommand:
    """Factory: compose three dependencies into one command."""
    return UploadKpiCommand(file_gate, parser, kpi_repo)