from typing import Annotated
from fastapi import APIRouter, UploadFile, Query, Depends, Form

from app.core.security import require_role
from app.models.request_model import TunkinRequest
from app.responses.builder import ResponseBuilder, get_response_builder
from app.tunkin.repository import TunkinRepository, get_tunkin_repository
from app.tunkin.commands import UploadKpiCommand, get_upload_kpi_command
from app.responses.schemas import User

router = APIRouter(
    prefix="/tunkin",
    tags=["Tunkin Endpoints"],
    responses={404: {"description": "Not found"}}
)

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
    periode: Annotated[str, Form()],
    file: UploadFile,
    user: Annotated[User, Depends(require_role(["payrollprocess"]))],
    response_builder: Annotated[ResponseBuilder, Depends(get_response_builder)],
    command: Annotated[UploadKpiCommand, Depends(get_upload_kpi_command)],
):
    result = await command.execute(periode, file)
    return response_builder.success(result.model_dump())