from typing import Annotated

from fastapi import APIRouter, UploadFile, Query, Depends, HTTPException
from starlette import status

from app.core.config import LOGGER
from app.models.request_model import TunkinRequest
from app.models.response_model import User, ResponseBuilder, get_response_builder
from app.core.security import require_role
from app.repositories.tunkin_repository import TunkinRepository, get_tunkin_repository
from app.repositories.kpi_repository import KPIRepository, get_kpi_repository
from app.services.file_gate import FileGate, get_file_gate
from app.services.kpi_sheet_parser import KPISheetParser, get_kpi_sheet_parser

router = APIRouter(
    prefix="/tunkin",
    tags=["Tunkin Endpoints"],
    responses={404: {"description": "Not found"}},
)


@router.get("/{periode}", summary="Data Tunkin")
def upload_file(periode: str,
                query: Annotated[TunkinRequest, Query()],
                user: Annotated[User, Depends(require_role(["payrollprocess"]))],
                response_builder: Annotated[ResponseBuilder, Depends(get_response_builder)],
                repository: Annotated[TunkinRepository, Depends(get_tunkin_repository)]):
    try:
        result = repository.fetch_page_data(periode, query)
        return response_builder.paginated(result)
    except HTTPException as e:
        LOGGER.error(e)
        return response_builder.from_exception(e)
    except Exception as e:
        LOGGER.error(e)
        return response_builder.from_exception(e)


@router.post("/upload", summary="Upload File Excel Tunkin")
async def upload_file(
    file: UploadFile,
    user: Annotated[User, Depends(require_role(["payrollprocess"]))],
    response_builder: Annotated[ResponseBuilder, Depends(get_response_builder)],
    file_gate: Annotated[FileGate, Depends(get_file_gate)],
    parser: Annotated[KPISheetParser, Depends(get_kpi_sheet_parser)],
    kpi_repo: Annotated[KPIRepository, Depends(get_kpi_repository)],
):
    try:
        data = await file_gate.check(file)
        records = parser.parse(data)
        result = kpi_repo.upsert_batch(records)
        return response_builder.success(result.model_dump())
    except HTTPException as e:
        if e.status_code == status.HTTP_400_BAD_REQUEST:
            return response_builder.bad_request(e.detail)
        if e.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR:
            return response_builder.internal_server_error(e.detail)
