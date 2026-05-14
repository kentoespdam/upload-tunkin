from typing import Annotated
from fastapi import APIRouter, Depends, Query

from app.core.security import require_role
from app.models.request_model import TunkinRequest, TunkinUploadRequest
from app.responses.builder import ResponseBuilder, get_response_builder
from app.tunkin.repository import TunkinRepository, get_tunkin_repository
from app.tunkin.commands import UploadKpiCommand, get_upload_kpi_command
from app.responses.schemas import User

router = APIRouter(
    prefix="/tunkin",
    tags=["Tunkin Endpoints"],
    responses={404: {"description": "Not found"}}
)

@router.get("/exists/{periode}", summary="Cek Data Tunkin")
def check_tunkin_exists(
    periode: str,
    user: Annotated[User, Depends(require_role(["payrollprocess"]))],
    response_builder: Annotated[ResponseBuilder, Depends(get_response_builder)],
    repository: Annotated[TunkinRepository, Depends(get_tunkin_repository)],
):
    count = repository.count_by_periode(periode)
    return response_builder.ok(data={"exists": count > 0, "count": count})

@router.get("/{periode}", summary="Data Tunkin")
def get_tunkin_data(
    periode: str,
    query: Annotated[TunkinRequest, Query()],
    user: Annotated[User, Depends(require_role(["payrollprocess"]))],
    response_builder: Annotated[ResponseBuilder, Depends(get_response_builder)],
    repository: Annotated[TunkinRepository, Depends(get_tunkin_repository)],
):
    result = repository.fetch_page_data(periode, query)
    return response_builder.paginated(result)

@router.post("/upload", summary="Upload File Excel Tunkin")
async def upload_tunkin_file(
    request: Annotated[TunkinUploadRequest, Depends(TunkinUploadRequest)],
    user: Annotated[User, Depends(require_role(["payrollprocess"]))],
    response_builder: Annotated[ResponseBuilder, Depends(get_response_builder)],
    command: Annotated[UploadKpiCommand, Depends(get_upload_kpi_command)],
):
    result = await command.execute(request.periode, request.file)
    return response_builder.success(result.model_dump())